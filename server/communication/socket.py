import socket
import logging
from communication.decoder import Decoder
from common import utils


class Socket:
    def __init__(self, port, listen_backlog):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        self.decoder = Decoder()

    def __recvall(self, client_socket):
        data = b''
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                raise BrokenPipeError("socket connection broken")

            data += chunk

            if b'\n' in chunk:
                break
            
        return  data 
    
    def __sendall (self, client_socket, data):
        total_sent = 0
        total_legth = len(data) 

        while total_sent < total_legth:
                sent = client_socket.send(data[total_sent:]) 
                if sent == 0:
                    raise BrokenPipeError("socket connection broken")
                
                total_sent += sent



    def handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            encoded_data = self.__recvall(client_sock)
            bets = self.decoder.decode_bets(encoded_data)
            
            utils.store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}.')
            
            encoded_response = self.decoder.encode_response(len(bets))
            self.__sendall(client_sock, encoded_response)
        
        except BrokenPipeError as e:
            logging.error(f"action: send_message | result: fail | error: BrokenPipeError: {e}")
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()



    def accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def cleanup(self):
        self._socket.close()
        logging.info("action: close_server_socket | result: success")

