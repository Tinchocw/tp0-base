import logging
import signal
from communication.socket import Socket
from common import utils
from communication.decoder import BetDeocdeError, Decoder


class Server:
    def __init__(self, port, listen_backlog):
        self.socket = Socket(port, listen_backlog)
        self.shutdown = False
        self.decoder = Decoder()


        signal.signal(signal.SIGTERM, self.__handle_sigterm)


    def __handle_sigterm(self, signum, frame):
        """
        Signal handler for SIGTERM

        This function is called when SIGTERM is received. It sets the
        shutdown flag to True, so the server can gracefully shutdown
        """

        logging.info("action: handle_sigterm | result: success")
        self.shutdown = True
        self.socket.close()


    def accept_new_connection(self):
        return self.socket.accept()

    def handle_client_connection(self, client_socket):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            encoded_data = client_socket.recvall()
            bets = self.decoder.decode_bets(encoded_data)
            
            utils.store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            
            encoded_response = self.decoder.encode_response(len(bets), 'success')
            client_socket.sendall(encoded_response)
        
        except BetDeocdeError as e:
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            encoded_response = self.decoder.encode_response(0, 'fail')
            client_socket.sendall(encoded_response)
            
        except BrokenPipeError as e:
            logging.error(f"action: send_message | result: fail | error: BrokenPipeError: {e}")
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")

        finally:
            client_socket.close()



    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        
        while self.shutdown is False:
            try:
                client_sock = self.accept_new_connection()
                self.handle_client_connection(client_sock)
            except OSError as e:
                if(self.shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")
        
