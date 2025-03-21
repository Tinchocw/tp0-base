package common

import (
	"bytes"
	"fmt"
	"io"
	"net"
	"strings"
	"time"

	"os"
	"os/signal"
	"strconv"
	"syscall"

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
	conn        net.Conn
	stopChannel chan struct{}
}

type UserBetConfig struct {
	Name     string
	LastName string
	Document string
	Birth    string
	Number   int
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

func (c *Client) loadUserBet() (UserBetConfig, error) {

	number, err := strconv.Atoi(os.Getenv("NUMERO"))
	if err != nil {
		return UserBetConfig{}, fmt.Errorf("invalid NUMERO: %v", err)
	}

	return UserBetConfig{
		Name:     os.Getenv("NOMBRE"),
		LastName: os.Getenv("APELLIDO"),
		Document: os.Getenv("DOCUMENTO"),
		Birth:    os.Getenv("NACIMIENTO"),
		Number:   number,
	}, nil
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

func (c *Client) deleteResources(signalChannel chan os.Signal) {
	c.deleteStopChannel()
	c.deleteSignalChannel(signalChannel)
	c.deleteClientSocket()
}

func (c *Client) deleteSignalChannel(signalChannel chan os.Signal) {
	if signalChannel != nil {
		signal.Stop(signalChannel)
		close(signalChannel)
		log.Infof("action: close_signal_channel | result: success | client_id: %v", c.config.ID)
	}

}

func (c *Client) deleteStopChannel() {
	if c.stopChannel != nil {
		close(c.stopChannel)
		log.Infof("action: close_notification_channel | result: success | client_id: %v", c.config.ID)
	}

}

func (c *Client) deleteClientSocket() {
	if c.conn != nil {
		c.conn.Close()
		log.Infof("action: close_socket | result: success | client_id: %v", c.config.ID)
	}

}

func (c *Client) handleSignals(sigChan chan os.Signal) {
	// Atach the signal channel to the signals SIGINT and SIGTERM
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Infof("action: signal_received | result: success | client_id: %v", c.config.ID)
		c.deleteResources(sigChan)
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

func (c *Client) sendAll(data string) error {
	var total_sent = 0
	var total_length = len(data)

	for total_sent < total_length {

		sent, err := c.conn.Write([]byte(data[total_sent:]))
		if err != nil {
			return fmt.Errorf("error sending data: %v", err)
		}
		if sent == 0 {
			return fmt.Errorf("Socket connection closed")
		}

		total_sent += sent
	}
	return nil
}

func (c *Client) recvAll(delimiter byte) ([]byte, error) {
	var buffer bytes.Buffer
	tmp := make([]byte, 1024)

	for {

		n, err := c.conn.Read(tmp)

		if n > 0 {
			// Escribimos los datos leídos (hasta n bytes) en el buffer principal
			buffer.Write(tmp[:n])

			if bytes.Contains(tmp[:n], []byte{delimiter}) {
				break
			}
		}

		if err != nil {
			if err == io.EOF {
				// Si se alcanza el final de la conexión, terminamos
				break
			}
			return nil, fmt.Errorf("error reading data: %w", err)
		}
	}
	return buffer.Bytes(), nil
}

func (c *Client) decodeData(data []byte) []string {

	dataString := string(data)

	parts := strings.Split(dataString, ",")

	for i := range parts {
		parts[i] = strings.TrimSpace(parts[i])
	}

	return parts
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	signalChannel := make(chan os.Signal, 1) // This channel will receive the signals
	c.handleSignals(signalChannel)

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Create the connection the server in every loop iteration. Send anj

		isReceived := c.isSignalReceived()
		if isReceived {
			return
		}

		userBet, err := c.loadUserBet()
		if err != nil {
			log.Errorf("action: load_clients_bet | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		c.createClientSocket()

		var data = fmt.Sprintf(
			"%v,%s,%s,%s,%s,%d\n",
			c.config.ID,
			userBet.Name,
			userBet.LastName,
			userBet.Document,
			userBet.Birth,
			userBet.Number,
		)

		err = c.sendAll(data)

		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %d",
			userBet.Document,
			userBet.Number,
		)

		msg, err := c.recvAll('\n')
		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
		decodedData := c.decodeData(msg)
		log.Infof("action: apuesta_almacenada | result: success | dni: %v | numero: %v",
			decodedData[0],
			decodedData[1],
		)

		c.deleteClientSocket()

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	c.deleteResources(signalChannel)
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
