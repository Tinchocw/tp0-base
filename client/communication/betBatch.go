package communication

type BetBatch struct {
	Bets []Bet
}

func NewBetBatch() *BetBatch {
	return &BetBatch{}
}

func (b *BetBatch) AddBet(bet Bet) {
	b.Bets = append(b.Bets, bet)
}

func (b *BetBatch) Serialize() []byte {
	var result string
	for i, bet := range b.Bets {
		result += bet.Serialize()

		if i < len(b.Bets)-1 {
			result += "&"
		}
	}
	result += "\n"
	return []byte(result)
}
