package common

import (
	"strconv"
	"strings"
	"time"

	"os"
	"os/signal"
	"syscall"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/communication"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config      ClientConfig
	socket      *communication.Socket
	stopChannel chan struct{}
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:      config,
		stopChannel: make(chan struct{}),
	}
	return client
}

func (c *Client) createClientSocket() error {
	var err error
	c.socket, err = communication.NewSocket(c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	return nil
}

func (c *Client) deleteClientSocket() {
	err := c.socket.Close()
	if err != nil {
		log.Errorf("action: close_socket | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}

}

func (c *Client) deleteStopChannel() {
	if c.stopChannel != nil {
		close(c.stopChannel)
		log.Infof("action: close_notification_channel | result: success | client_id: %v", c.config.ID)
	}

}

func (c *Client) deleteResources() {
	c.deleteStopChannel()
	c.deleteClientSocket()
}

func (c *Client) handleSignals(sigChan chan os.Signal) {
	// Atach the signal channel to the signals SIGINT and SIGTERM
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Infof("action: signal_received | result: success | client_id: %v", c.config.ID)
		c.deleteResources()
	}()

}

func (c *Client) isSignalReceived() bool {
	select {
	case <-c.stopChannel:
		log.Infof("action: stop_received | result: success | client_id: %v", c.config.ID)
		return true
	default:
	}
	return false
}

// Esta función la tengo que sacar de acá
func (c *Client) decodeData(data []byte) []string {

	dataString := string(data)

	parts := strings.Split(dataString, ",")

	for i := range parts {
		parts[i] = strings.TrimSpace(parts[i])
	}

	return parts
}

func (c *Client) decodeResponse(data []byte) int {
	// Convierte los datos de bytes a string
	dataString := string(data)

	// Elimina el salto de línea al final
	dataString = strings.TrimSpace(dataString)

	// Convierte la cadena a un entero
	betAmount, err := strconv.Atoi(dataString)
	if err != nil {
		log.Errorf("action: decode_response | result: fail | error: %v", err)
		return 0 // Devuelve un valor por defecto en caso de error
	}

	return betAmount
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	signalChannel := make(chan os.Signal, 1) // This channel will receive the signals
	c.handleSignals(signalChannel)

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	parser, err := NewParser("bets.txt", 10, c.config.ID)
	if err != nil {
		log.Errorf("action: create_bet_parser | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {

		isReceived := c.isSignalReceived()
		if isReceived {
			return
		}

		batch, err := parser.ReadBatch()
		if err != nil {
			log.Errorf("action: read_batch | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			parser.Close()
			return
		}

		batchSerialized := batch.Serialize()

		c.createClientSocket()

		err = c.socket.SendAll(batchSerialized)

		if err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		response, err := c.socket.RecvAll()
		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		amount := c.decodeData(response)
		log.Infof("action: apuestas_almacenada | result: success | cantidad: %v", amount)

		c.deleteClientSocket()

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	c.deleteResources()
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
