package common

import (
	"bufio"
	"io"
	"os"
	"testing"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/communication"
)

func TestReadBatchHandlesLeftoverLine(t *testing.T) {

	aStringBet := "A,B,00000000,2000-01-01,0"
	anotherStringBet := "A,B,00000001,2000-01-01,1"
	content := aStringBet + "\n" + anotherStringBet + "\n"

	aBet := communication.NewBet(1, "A", "B", "00000000", "2000-01-01", 0)
	anotherBet := communication.NewBet(1, "A", "B", "00000001", "2000-01-01", 1)

	file, err := os.CreateTemp("", "testfile")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(file.Name()) // Limpia el archivo después de la prueba

	_, err = file.WriteString(content)
	if err != nil {
		t.Fatalf("Failed to write to temp file: %v", err)
	}
	file.Close()

	// Reabre el archivo para lectura
	file, err = os.Open(file.Name())
	if err != nil {
		t.Fatalf("Failed to open temp file: %v", err)
	}
	defer file.Close()

	// Configura el Parser
	parser := &Parser{
		file:         file,
		maxBatch:     2, // La idea es que se procese un batch de 2 líneas por llamda
		bufReader:    bufio.NewReader(file),
		agency:       1,
		leftoverLine: "",
		maxSize:      27, // Tamaño que representa la primera línea	+ 1 byte
	}

	// Llama a ReadBatch con un límite de tamaño
	batch, err := parser.ReadBatch()
	if err != nil {
		t.Fatalf("ReadBatch failed: %v", err)
	}

	// Verifica que solo se haya procesado la primera línea
	if len(batch) != 1 {
		t.Errorf("Expected 1 bet in batch, got %d", len(batch))
	}
	if batch[0].Equals(aBet) == false {
		t.Errorf("Expected first bet to be %v, got %v", aBet, batch[0])
	}

	// Verifica que la segunda línea se haya guardado en leftoverLine
	if parser.leftoverLine != anotherStringBet+"\n" {
		t.Errorf("Expected leftoverLine to be '%s', got '%s'", anotherStringBet, parser.leftoverLine)
	}

	// Llama a ReadBatch nuevamente
	batch, err = parser.ReadBatch()
	if err != nil && err != io.EOF {
		t.Fatalf("ReadBatch failed on second call: %v", err)
	}

	// Verifica que la segunda línea se procese en la siguiente llamada
	if len(batch) != 1 {
		t.Errorf("Expected 1 bet in batch, got %d", len(batch))
	}
	if batch[0].Equals(anotherBet) == false {
		t.Errorf("Expected first bet to be %v, got %v", aBet, batch[0])
	}

}
