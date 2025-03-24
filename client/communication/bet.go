package communication

import (
	"fmt"
	"strconv"
	"strings"
)

type Bet struct {
	Agency   int
	Name     string
	LastName string
	Document string
	Birth    string
	Number   int
}

func NewBet(agency int, name, lastName, document, birth string, number int) *Bet {
	return &Bet{
		Agency:   agency,
		Name:     name,
		LastName: lastName,
		Document: document,
		Birth:    birth,
		Number:   number,
	}
}

func NewBetFromLine(line string, agency int) (*Bet, error) {

	fields := strings.Split(line, ",")
	if len(fields) != 5 {
		return nil, fmt.Errorf("invalid bet line: %s", line)
	}

	number, err := strconv.Atoi(strings.TrimSpace(fields[4]))

	if err != nil {
		return nil, fmt.Errorf("invalid number: %s", fields[4])
	}

	return NewBet(agency, fields[0], fields[1], fields[2], fields[3], number), nil
}

func (b *Bet) Serialize() string {

	return fmt.Sprintf("%s,%s,%s,%s,%s,%s", fmt.Sprint(b.Agency), b.Name, b.LastName, b.Document, b.Birth, fmt.Sprint(b.Number))
}
