import logging
import signal
from common import utils
from communication.socket import Socket


class Server:
    def __init__(self, port, listen_backlog):
        self.socket = Socket(port, listen_backlog)
        self.shutdown = False

        signal.signal(signal.SIGTERM, self.__handle_sigterm)


    def __handle_sigterm(self, signum, frame):
        """
        Signal handler for SIGTERM

        This function is called when SIGTERM is received. It sets the
        shutdown flag to True, so the server can gracefully shutdown
        """

        logging.info("action: handle_sigterm | result: success")
        self.shutdown = True
        self.__cleanup()


        

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        
        while self.shutdown is False:
            try:
                client_sock = self.socket.accept_new_connection()
                self.socket.handle_client_connection(client_sock)
            except OSError as e:
                if(self.shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")
        
