import socket
import logging


class Socket:
    def __init__(self, address, listen_backlog, sock=None):
        if sock is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind(('', address))
            self._socket.listen(listen_backlog)
        else:
            self._socket = sock


    @classmethod
    def createServerSocket(cls, address, listen_backlog):
        return cls(address, listen_backlog)
    
    @classmethod
    def from_socket(cls, address, socket):
        return cls(address, None, socket)
    

    def recvall(self):
        data = b''
        while True:
            chunk = self._socket.recv(1024)
            if not chunk:
                raise BrokenPipeError("socket connection broken")

            data += chunk

            if b'\n' in chunk:
                break
            
        return  data 
    
    def sendall (self, data):
        total_sent = 0
        total_legth = len(data) 

        while total_sent < total_legth:
                sent = self._socket.send(data[total_sent:]) 
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
        c, addr = self._socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return Socket.from_socket(addr, c)
    

    def close(self):
        self._socket.close()
        logging.info("action: close_server_socket | result: success")

