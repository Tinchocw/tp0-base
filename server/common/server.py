from common import utils
import logging
import signal
from communication.socket import Socket
from communication.decoder import Decoder


class Server:
    def __init__(self, port, listen_backlog):
        self.__socket = Socket(port, listen_backlog)
        self.__shutdown = False
        self.__decoder = Decoder()

        signal.signal(signal.SIGTERM, self.__handle_sigterm)


    def __handle_sigterm(self, signum, frame):
        """
        Signal handler for SIGTERM

        This function is called when SIGTERM is received. It sets the
        shutdown flag to True, so the server can gracefully shutdown
        """

        logging.info("action: handle_sigterm | result: success")
        self.__shutdown = True
        self.__socket.close()


    def handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            encoded_data = client_sock.recvall()
            bet = self.__decoder.decode_data(encoded_data)

            utils.store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}.')

            client_sock.sendall(self.__decoder.encode_data(bet))
        
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
        return self.__socket.accept()

        

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        
        while self.__shutdown is False:
            try:
                client_sock = self.accept_new_connection()
                self.handle_client_connection(client_sock)
            except OSError as e:
                if(self.__shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")
        
