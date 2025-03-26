import socket
import logging

END_MESSAGE_DELIMITER = b'\n'


class Socket:
    def __init__(self, address, listen_backlog, sock=None):
        if sock is None:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.bind(('', address))
            self.__socket.listen(listen_backlog)
            self.__overflow = ""
        else:
            self.__socket = sock


    @classmethod
    def createServerSocket(cls, address, listen_backlog):
        return cls(address, listen_backlog)
    
    @classmethod
    def from_socket(cls, address, socket):
        return cls(address, None, socket)
    


# Recibo un mensaje
# ese mensaje contiene un /n en el medio, por lo que tengo más información despues 
# 
    def recvall(self):
        while END_MESSAGE_DELIMITER not in self.__overflow:
            chunk = self.__socket.recv(1024)
            if not chunk:
                if self.__overflow :
                    message = self.__overflow
                    self.__overflow = ""
                    return message
                else: 
                    raise BrokenPipeError("socket connection broken")

            self.__overflow += chunk
        
        message, self.__overflow = self.__overflow.split(END_MESSAGE_DELIMITER, 1)
            
        return  message 
    
    def sendall (self, data):
        total_sent = 0
        total_legth = len(data) 

        while total_sent < total_legth:
                sent = self.__socket.send(data[total_sent:]) 
                if sent == 0:
                    raise BrokenPipeError("socket connection broken")
                
                total_sent += sent

    def accept(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self.__socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return Socket.from_socket(addr, c)
    

    def close(self):
        self.__socket.close()
        logging.info("action: close_server_socket | result: success")

