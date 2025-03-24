from common import utils

class BetDeocdeError(Exception):
    """Excepción personalizada para errores de decodificación de apuestas."""
    def __init__(self, message):
        super().__init__(message)

     
class Decoder:
    def __init__(self):
        pass 
    
        
    def __decode_bet(self, data):
        decoded_data = data.split(',')
        if len(decoded_data) != 6:
                raise BetDeocdeError("Invalid data length")

        return utils.Bet(decoded_data[0], decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5]) 
    

    def decode_bets(self, data):
        decode_bets = data.decode('utf-8').rstrip().split('&')
        bets = []

        for bet in decode_bets:
            bets.append(self.__decode_bet(bet))
        
        return bets
    

    def encode_response(self, bet_amount, status):
        return f"{status},{bet_amount}\n".encode('utf-8')