import socket
import logging
import signal
import sys
import utils 

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.shutdown = False

        signal.signal(signal.SIGTERM, self.__handle_sigterm)

    def __cleanup(self):
        self._server_socket.close()
        logging.info("action: close_server_socket | result: success")


    def __handle_sigterm(self, signum, frame):
        """
        Signal handler for SIGTERM

        This function is called when SIGTERM is received. It sets the
        shutdown flag to True, so the server can gracefully shutdown
        """

        logging.info("action: handle_sigterm | result: success")
        self.shutdown = True
        self.__cleanup()

    def __decode_data(self, data):
        decoded_data = data.decode('utf-8').rstrip().split(',')
        if len(decoded_data) != 6:
                raise ValueError("Invalid data length")
        
        return decoded_data
        

    def recvall(self, sock):
        data = b''
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break

            data += chunk

            if b'\n' in chunk:
                break
            
        return  data 
    
    def sendall (self, socket, data):
        total_sent = 0
        total_legth = len(data) 

        while total_sent < total_legth:
                sent = socket.send(data[total_sent:]) 
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                
                total_sent += sent
        
    
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        
        while self.shutdown is False:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError as e:
                if(self.shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")
        



    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            encoded_data = self.recvall(client_sock)
            decoded_data = self.__decode_data(encoded_data)

            self.__process_bet(decoded_data)    

            dni = decoded_data[3]
            bet_number = decoded_data[5]

            
            response = f"{dni},{bet_number}\n"
            self.sendall(client_sock, response.encode('utf-8'))

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __process_bet(self, decoded_data):
        bet = utils.Bet(decoded_data[0], decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5]) 
        utils.store_bets([bet])
        logging.info(f'action: apuesta_almacenada | result: success | dni: {decoded_data[3]} | numero: {decoded_data[3]}.')

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
