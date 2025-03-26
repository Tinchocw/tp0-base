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
        self.__finished_clients = 0  # Contador de clientes que finalizaron
        self.__total_clients = total_clients  # Número total de agencias esperadas
        self.__client_sockets = {}  # Diccionario para almacenar los sockets de los clientes por agencia

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
        
        finish_field = False

        while not finish_field:
            try:
                encoded_data = client_socket.recvall()

                # la idea es que agarro lo que viene, segun el header veo la información que viene y proceso de la forma correspondiente 
                # en el caso de que sea una BET sigo recibiendo en el otro caso cierro el loop 

                header, data = self.__serializer.deserialize_response(encoded_data)
                if header == 'BET':
                    bets = self.__serializer.deserialize_bets(data)
                    utils.store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                
                    serialize_response = self.__serializer.serialize_amount_response(len(bets), 'success')
                    client_socket.sendall(serialize_response)
                elif header == 'END':
                    finish_field = True
                    agency_id = self.__serializer.deserialize_end_request(data) #tiene que recibir este mensaje de las 5 agenicas para poder hacer el sorteo

                    logging.info(f'action: fin_apuestas | result: success | agencia: {agency_id}')
                    # En el caso de que no tenga la dirección lo que tengo que hacer es tener un set de clientes en el que cuando se llega a la cantidad esperada se corta 
                    self.__finished_clients += 1  
                    self.__client_sockets[agency_id] = client_socket 
                    
                elif header == 'WIN':
                    self.perform_draw()


            except BetDeserializeError as e:
                logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                serialize_response = self.__serializer.serialize_amount_response(0, 'fail')
                client_socket.sendall(serialize_response)
                client_socket.close()
            
            except DeserializeError as e:
                logging.error(f"action: deserialization | result: fail | error: DeserializeError: {e}")
                client_socket.close()
                
            except BrokenPipeError as e:
                logging.error(f"action: send_message | result: fail | error: BrokenPipeError: {e}")
                client_socket.close()

            except OSError as e:
                logging.error("action: receive_message | result: fail | error: {e}")
                client_socket.close()


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

        

    def perform_draw(self):
        """
        Realiza el sorteo una vez que todos los clientes han finalizado.
        """
        winners = {}  # Diccionario para almacenar los ganadores por agencia

        # Carga todas las apuestas y determina los ganadores

        if self.__finished_clients == self.__total_clients:
            for bet in utils.load_bets():
                if utils.has_won(bet):
                    if bet.agency not in winners:
                        winners[bet.agency] = []
                    winners[bet.agency].append(bet.document)

            logging.info(f"Sorteo completado. Ganadores: {winners}")

            # Envía los resultados a cada cliente
            for agency_id, client_socket in self.__client_sockets.items():
                try:
                    result_message = self.__serializer.serialize_winners(winners.get(agency_id, []))
                    logging.info(f"Enviando resultados a la agencia {agency_id}")
                    logging.info(f"result_message: {result_message}")

                    client_socket.sendall(result_message)
                except BrokenPipeError as e:
                    logging.error(f"action: send_result | result: fail | error: BrokenPipeError: {e}")
                except OSError as e:
                    logging.error(f"action: send_result | result: fail | error: {e}")

                finally:
                    client_socket.close()
