from common import utils

class Decoder:
    def __init__(self):
        pass 
    
    def decode_data(self, data):
        decoded_data = data.decode('utf-8').rstrip().split(',')
        if len(decoded_data) != 6:
                raise ValueError("Invalid data length")

        return utils.Bet(decoded_data[0], decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5]) 
    
    def encode_data(self, bet):
        return f"{bet.document},{bet.number}\n".encode('utf-8')