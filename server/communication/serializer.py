from common import utils

BET_HEADER = "BET"
END_HEADER = "END"
WINNER_HEADER = "WIN"


class BetDeserializeError(Exception):
    """Excepción personalizada para errores de decodificación de apuestas."""
    def __init__(self, message):
        super().__init__(message)

     
class Serializer:
    def __init__(self):
        pass 
    
        
    def __deserialize_bet(self, data):
        decoded_data = data.split(',')
        if len(decoded_data) != 6:
                raise BetDeserializeError("Invalid data length")

        return utils.Bet(decoded_data[0], decoded_data[1], decoded_data[2], decoded_data[3], decoded_data[4], decoded_data[5]) 
    

    def deserialize_bets(self, data):
        haedar, bets = data.decode('utf-8').rstrip().split(' ', 1)
        if haedar != BET_HEADER:
            raise BetDeserializeError("Invalid header")
        
        deserialize_bets = bets.rstrip().split('&')

        bets = []

        for bet in deserialize_bets:
            bets.append(self.__deserialize_bet(bet))
        
        return bets
    
    def deserialize_winner_request(self, data):
        haedar = data.decode('utf-8').rstrip().split(' ', 1)[0]
        if haedar != WINNER_HEADER:
            raise BetDeserializeError("Invalid header, expected WIN")
        
        return haedar
    
    def deserialize_end_request(self, data):
        haedar, agency_id = data.decode('utf-8').rstrip().split(' ', 1)
        if haedar != END_HEADER:
            raise BetDeserializeError("Invalid header, expected END")
        
        return int(agency_id)
    

    def serialize_response(self, bet_amount, status):
        return f"{status},{bet_amount}\n".encode('utf-8')