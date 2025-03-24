package common

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strconv"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/communication"
)

const maxSize = 8192 // 8KB

type Parser struct {
	file         *os.File
	maxBatch     int
	bufReader    *bufio.Reader
	agency       int
	leftoverLine string
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

func (p *Parser) ReadBatch() ([]communication.Bet, error) {
	batch := make([]communication.Bet, 0)

	totalSize := 0
	header := "BET "
	totalSize += len(header)

	// Procesar línea sobrante de la ejecución anterior, si existe
	if p.leftoverLine != "" {
		if totalSize+len(p.leftoverLine) > maxSize {
			return batch, nil // Si la línea ya supera el límite, no se puede procesar
		}
		bet, err := communication.NewBetFromLine(p.leftoverLine, p.agency)
		if err == nil {
			batch = append(batch, *bet)
			totalSize += len(p.leftoverLine)
		} else {
			log.Warning(err)
		}
		p.leftoverLine = ""
	}

	for i := 0; i < p.maxBatch; i++ {
		line, err := p.bufReader.ReadString('\n')

		if err != nil {
			if err == io.EOF {
				if len(batch) > 0 {
					return batch, nil
				}
				return nil, io.EOF // Devuelve EOF si no hay apuestas
			}
			return nil, err
		}

		// Si agregar la línea supera el límite, guardarla para la próxima llamada
		if totalSize+len(line) > maxSize {
			p.leftoverLine = line
			break
		}

		bet, err := communication.NewBetFromLine(line, p.agency)
		if err != nil {
			log.Warning(err)
			continue
		}
		batch = append(batch, *bet)
		totalSize += len(line)
	}

	return batch, nil

}

func (p *Parser) Close() error {
	if p.file != nil {
		log.Infof("action: close_file | result: success | file: %v", p.file.Name())
		return p.file.Close()
	} else {
		log.Infof("action: close_file | result: fail | file: %v", p.file.Name())
	}
	return nil
}
