import logging
import signal
import threading
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

        self.__file_lock = threading.Lock()
        self.__counter_lock = threading.Lock()
        self.client__threads = []

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

        for thread in self.client__threads:
            thread.join()
        
        self.client__threads = []

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
        
        with self.__file_lock: 
            utils.store_bets(bets)
        
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                    
        serialize_response = self.__serializer.serialize_amount_response(len(bets), 'success')
        client_socket.sendall(serialize_response)
        return bets

    def __process_end_request(self, data):
        agency_id = self.__serializer.deserialize_agency_id(data) 
        logging.info(f'action: fin_apuestas | result: success | agencia: {agency_id}')
        with self.__counter_lock: 
            self.__finished_clients += 1  

    def __process_win_request(self, client_socket, data):

        agency_id = self.__serializer.deserialize_agency_id(data)
        
        with self.__counter_lock:
            all_clients_finished = self.__finished_clients == self.__total_clients

        if all_clients_finished:
                winners = self.__perfrom_draw(agency_id) 
                logging.info(f'action: sorteo | result: success | ganadores: {winners}')           
                result_message = self.__serializer.serialize_winners(winners)
                client_socket.sendall(result_message)
        else:
            not_ready_message = self.__serializer.serialize_not_ready()
            client_socket.sendall(not_ready_message)

    def __perfrom_draw(self, agency_id):
        winners = []
        
        with self.__file_lock:
            for bet in utils.load_bets():
                if utils.has_won(bet) and bet.agency == agency_id:
                    winners.append(bet.document)
        
        if not winners:
            winners.append("empty")
                
        return winners


    def run(self):
    
        while self.__shutdown is False:
            try:
                
                client_sock = self.accept_new_connection()
                
                client_thread = threading.Thread(
                    target=self.handle_client_connection, args=(client_sock,)
                )
                client_thread.start()

                self.client__threads.append(client_thread)

                self.__reap_clients
            except OSError as e:
                if(self.__shutdown):
                    break
                logging.error(f"action: accept_connections | result: fail | error: {e}")



    def __reap_clients(self):
        
        for client in self.client__threads:
            if not client.is_alive():
                client.join()
                self.client__threads.remove(client)        
                logging.info("action: join client | result: success")
                