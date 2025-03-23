package common

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
	for _, bet := range b.Bets {
		result += bet.Serialize() + "&"
	}
	result += "\n"
	return []byte(result)
}

// for
// leo linea y creo una Bet
// agrego a la lista de bets
// leo otra vez y así

//ahora tengo que encodear toda esta info, lo hago como

// campo, campo, campo, campo, campo & campo, campo, campo, campo, campo /n

// se la paso al parser para que haga lo que tiene que hacer
// se lo paso al socket para que lo envie
// del otro lado lo tengo que decodificar
