package communication

import (
	"fmt"
	"strings"
)

const betHeader = "BET"
const endHeader = "END"
const winnerHeader = "WIN"

// Serializer is a placeholder struct for serialization logic
type Serializer struct{}

func NewSerializer() *Serializer {
	return &Serializer{}
}

func (*Serializer) SerializeBet(betBatch []Bet) []byte {
	var result string
	result += betHeader + " "

	for i, bet := range betBatch {
		result += bet.Serialize()

		if i < len(betBatch)-1 {
			result += "&"
		}
	}
	result += "\n"
	return []byte(result)
}

func (s *Serializer) SerializeEnd(client_id string) []byte {
	return []byte(endHeader + " " + client_id + "\n")
}

func (s *Serializer) separateHeader(data []byte) (string, string) {
	dataString := strings.TrimSpace(string(data))
	parts := strings.SplitN(dataString, " ", 2)
	return parts[0], parts[1]
}

func (s *Serializer) DeserializeWinner(data []byte) (int, error) {
	header, dataString := s.separateHeader(data)
	dataString = strings.TrimSpace(dataString)

	if header != winnerHeader {
		return 0, fmt.Errorf("invalid response format: %s", dataString)
	}

	parts := strings.Split(dataString, ",")

	return len(parts), nil
}

func (s *Serializer) DeserializeBatchAmount(data []byte) (string, string, error) {
	header, dataString := s.separateHeader(data)
	dataString = strings.TrimSpace(dataString)

	if header != betHeader {
		return "", "", fmt.Errorf("invalid response format: %s", dataString)
	}

	// Divide el mensaje en "status" y "bet_amount" usando la coma como separador
	parts := strings.Split(dataString, ",")
	if len(parts) != 2 {
		return "", "", fmt.Errorf("invalid response format: %s", dataString)
	}

	result := parts[0]
	betAmount := parts[1]
	return result, betAmount, nil
}
