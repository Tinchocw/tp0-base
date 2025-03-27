import logging
import signal
from communication.socket import Socket
from common import utils
from communication.serializer import BetDeserializeError, DeserializeError, Serializer


class Server:
    def __init__(self, port, listen_backlog, total_clients):
        self.__socket = Socket(port, listen_backlog)
        self.__shutdown = False
        self.__serializer = Serializer()
        self.__finished_clients = 0  
        self.__total_clients = total_clients  

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


    def accept_new_connection(self):
        return self.__socket.accept()

    def handle_client_connection(self, client_socket):
        
        bets = []
        try: 
            while True:
                
                    encoded_data = client_socket.recvall()

                    header, data = self.__serializer.deserialize_response(encoded_data)
                    if header == 'BET':
                        bets = self.__process_bet_request(client_socket, data)
                    elif header == 'END':
                        self.__process_end_request(data) 
                        
                    elif header == 'WIN':
                        self.__process_win_request(client_socket, data)
                        break


        except BetDeserializeError as e:
            logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            serialize_response = self.__serializer.serialize_amount_response(0, 'fail')
            client_socket.sendall(serialize_response)
        
        except DeserializeError as e:
            logging.error(f"action: deserialization | result: fail | error: DeserializeError: {e}")
            
        except BrokenPipeError as e:
            logging.error(f"action: send_message | result: fail | error: BrokenPipeError: {e}")

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")

        finally:
            client_socket.close()

    def __process_bet_request(self, client_socket, data):
        bets = self.__serializer.deserialize_bets(data)
        utils.store_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                    
        serialize_response = self.__serializer.serialize_amount_response(len(bets), 'success')
        client_socket.sendall(serialize_response)
        return bets

    def __process_end_request(self, data):
        agency_id = self.__serializer.deserialize_agency_id(data) 
        logging.info(f'action: fin_apuestas | result: success | agencia: {agency_id}')
        self.__finished_clients += 1  

    def __process_win_request(self, client_socket, data):

        agency_id = self.__serializer.deserialize_agency_id(data)
        
        if self.__finished_clients == self.__total_clients:

            winners = self.__perfrom_draw()            
            result_message = self.__serializer.serialize_winners(winners.get(agency_id, ["empty"]))
            client_socket.sendall(result_message)
            
        else :
            not_ready_message = self.__serializer.serialize_not_ready()
            client_socket.sendall(not_ready_message)

    def __perfrom_draw(self):
        winners = {}
        for bet in utils.load_bets():
            if utils.has_won(bet):
                if bet.agency not in winners:
                    winners[bet.agency] = []
                winners[bet.agency].append(bet.document)

        return winners


    def run(self):
    
        while self.__shutdown is False:
            try:
                client_sock = self.accept_new_connection()
                self.handle_client_connection(client_sock)
            except OSError as e:
                if(self.__shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")

        
