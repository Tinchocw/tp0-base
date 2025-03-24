package communication

import (
	"fmt"
	"strings"
)

// Serializer is a placeholder struct for serialization logic
type Serializer struct{}

func NewSerializer() *Serializer {
	return &Serializer{}
}

func (*Serializer) Serialize(betBatch []Bet) []byte {
	var result string
	for i, bet := range betBatch {
		result += bet.Serialize()

		if i < len(betBatch)-1 {
			result += "&"
		}
	}
	result += "\n"
	return []byte(result)
}

func (*Serializer) Deserialize(data []byte) (string, string, error) {

	dataString := strings.TrimSpace(string(data))

	// Divide el mensaje en "status" y "bet_amount" usando la coma como separador
	parts := strings.Split(dataString, ",")
	if len(parts) != 2 {
		return "", "", fmt.Errorf("invalid response format: %s", dataString)
	}

	result := parts[0]
	betAmount := parts[1]
	return result, betAmount, nil
}
