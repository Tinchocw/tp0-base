package common

import (
	"errors"
	"io"
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
	MaxAmount     int
}

// Client Entity that encapsulates how
type Client struct {
	config      ClientConfig
	socket      *communication.Socket
	stopChannel chan struct{}
	serializer  *communication.Serializer
}

var ErrSignalReceived = errors.New("signal received")

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:      config,
		stopChannel: make(chan struct{}),
		serializer:  communication.NewSerializer(),
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

	log.Info("creando nuevo socket")
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

func (c *Client) Shutdown() {
	c.deleteStopChannel()
	c.deleteClientSocket()
}

func (c *Client) handleSignals(sigChan chan os.Signal) {
	// Atach the signal channel to the signals SIGINT and SIGTERM
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Infof("action: signal_received | result: success | client_id: %v", c.config.ID)
		c.Shutdown()
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

func (c *Client) Run() {

	signalChannel := make(chan os.Signal, 1) // This channel will receive the signals
	c.handleSignals(signalChannel)

	err := c.SendAllBets()
	if err != nil {
		return
	}
	log.Infof("Todas las apuestas han sido enviadas")
	err = c.NotifyAllBetsHaveBeenSent()
	if err != nil {
		return
	}

	log.Info("esperando respuesta")
	err = c.handleWinnerRequest()
	if err != nil {
		return
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

// SendAllBets Send messages to the client until some time threshold is met
func (c *Client) SendAllBets() error {
	var err error = nil

	parser, err := NewParser(c.config.ID, c.config.MaxAmount, maxSize)
	if err != nil {
		log.Errorf("action: create_bet_parser | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	endOfFile := false

	err = c.createClientSocket()
	if err != nil {
		return err
	}

	for !endOfFile {

		isReceived := c.isSignalReceived()
		if isReceived {
			return ErrSignalReceived
		}

		batch, err := parser.ReadBatch()
		if err != nil {
			if err == io.EOF {
				log.Infof("action: end_of_file | result: success | client_id: %v", c.config.ID)
				endOfFile = true
				continue

			}
			log.Errorf("action: read_batch | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err

		}

		batchSerialized := c.serializer.SerializeBet(batch)

		err = c.socket.SendAll(batchSerialized)

		if err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		response, err := c.socket.RecvAll()
		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		result, amount, err := c.serializer.DeserializeBatchAmount(response)
		if err != nil {
			log.Errorf("action: deserialize_response | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		log.Infof("action: apuestas_almacenada | result: %v | cantidad: %v", result, amount)
	}
	return nil
}

func (c *Client) NotifyAllBetsHaveBeenSent() error {
	var err error = nil

	isReceived := c.isSignalReceived()
	if isReceived {
		return ErrSignalReceived
	}

	err = c.socket.SendAll(c.serializer.SerializeEndRequest(c.config.ID))
	if err != nil {
		log.Errorf("action: send_end | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	return err
}

func (c *Client) handleWinnerRequest() error {
	var err error = nil
	isWinAviable := false
	sleepTime := 200 * time.Millisecond

	for !isWinAviable {
		isReceived := c.isSignalReceived()
		if isReceived {
			return ErrSignalReceived
		}
		if c.socket.IsClosed() {

			err = c.createClientSocket()
			if err != nil {
				return err
			}
		}

		err = c.socket.SendAll(c.serializer.SerializeWinnerRequest(c.config.ID))
		if err != nil {
			log.Errorf("action: send_end | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		winnerSerializeResponse, err := c.socket.RecvAll()
		if err != nil {
			log.Errorf("action: receive_winner | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		isWinAviable, winnerAmount, err := c.serializer.DeserializeWinnerResponse(winnerSerializeResponse, c.config.ID)
		if err != nil {
			log.Errorf("action: deserialize_winner | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		if isWinAviable {
			log.Infof("action: winner_obtained | result: success | client_id: %v | amount: %v", c.config.ID, winnerAmount)

		} else {
			log.Infof("action: winner_not_obtained | result: success | client_id: %v", c.config.ID)
			time.Sleep(sleepTime)
			sleepTime = sleepTime * 2
		}

		c.socket.Close()
	}
	return nil

}
