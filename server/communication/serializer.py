from common import utils

class BetDeserializeError(Exception):
    """Excepción personalizada para errores de decodificación de apuestas."""
    def __init__(self, message):
        super().__init__(message)

     
class Serializer:
    def __init__(self):
        pass 
    
        
    def __serialize_bet(self, data):
        decoded_data = data.split(',')
        if len(decoded_data) != 6:
                raise BetDeserializeError("Invalid data length")

        return utils.Bet(decoded_data[0], decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5]) 
    

    def deserialize_bets(self, data):
        deserialize_bets = data.decode('utf-8').rstrip().split('&')
        bets = []

        for bet in deserialize_bets:
            bets.append(self.__serialize_bet(bet))
        
        return bets
    

    def serialize_response(self, bet_amount, status):
        return f"{status},{bet_amount}\n".encode('utf-8')