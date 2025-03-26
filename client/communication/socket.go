package communication

import (
	"bytes"
	"fmt"
	"io"
	"net"
)

type Socket struct {
	conn net.Conn
}

func NewSocket(address string) (*Socket, error) {
	conn, err := net.Dial("tcp", address)
	if err != nil {
		return nil, fmt.Errorf("error connecting to server: %v", err)
	}

	return &Socket{conn: conn}, nil
}

func (s *Socket) SendAll(data []byte) error {
	var total_sent = 0
	var total_length = len(data)

	for total_sent < total_length {

		sent, err := s.conn.Write((data[total_sent:]))
		if err != nil {
			return fmt.Errorf("error sending data: %v", err)
		}
		if sent == 0 {
			return fmt.Errorf("socket connection closed")
		}

		total_sent += sent
	}
	return nil
}

func (s *Socket) RecvAll() ([]byte, error) {
	var buffer bytes.Buffer
	tmp := make([]byte, 1024)

	for {

		n, err := s.conn.Read(tmp)

		if n > 0 {
			// Escribimos los datos leídos (hasta n bytes) en el buffer principal
			buffer.Write(tmp[:n])

			if bytes.Contains(tmp[:n], []byte{'\n'}) {
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

func (s *Socket) IsClosed() bool {
	return s.conn == nil
}

func (s *Socket) Close() error {
	if s.IsClosed() {
		return fmt.Errorf("socket connection is already closed")
	}
	s.conn.Close()
	s.conn = nil
	return nil
}
