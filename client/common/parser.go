package common

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strconv"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/communication"
)

type Parser struct {
	file      *os.File
	maxBatch  int
	bufReader *bufio.Reader
	agency    int
}

func NewParser(agency string, maxBatch int) (*Parser, error) {
	filename := fmt.Sprintf("/data/agency-%s.csv", agency)
	log.Infof("Opening file %s", filename)
	file, err := os.Open(filename)
	if err != nil {

		return nil, err
	}

	agency_, err := strconv.Atoi(agency)
	if err != nil {
		return nil, err
	}

	return &Parser{
		file:      file,
		maxBatch:  maxBatch,
		bufReader: bufio.NewReader(file),
		agency:    agency_,
	}, nil
}

func (p *Parser) ReadBatch() (*communication.BetBatch, error) {
	batch := communication.NewBetBatch()

	for i := 0; i < p.maxBatch; i++ {
		line, err := p.bufReader.ReadString('\n')

		if err != nil {
			if err == io.EOF {
				if len(batch.Bets) > 0 {
					return batch, nil
				}
				return nil, io.EOF // Devuelve EOF si no hay apuestas
			}
			return nil, err
		}

		bet, err := communication.NewBetFromLine(line, p.agency)
		if err != nil {
			log.Warning(err)
			continue
		}

		batch.AddBet(*bet)
	}

	return batch, nil

}

func (p *Parser) Close() error {
	if p.file != nil {
		return p.file.Close()
	}
	return nil
}
