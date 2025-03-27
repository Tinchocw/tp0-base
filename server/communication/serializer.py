from common import utils

BET_HEADER = "BET"
END_HEADER = "END"
WINNER_HEADER = "WIN"
NOT_READY_HEADER = "NOT_READY"



class BetDeserializeError(Exception):
    """Excepción personalizada para errores de decodificación de apuestas."""
    def __init__(self, message):
        super().__init__(message)


class DeserializeError(Exception):
    """Excepción personalizada para errores de decodificación de ganadores."""
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
    


    def deserialize_response(self, data):
        header, data = data.decode('utf-8').rstrip().split(' ', 1)
        return header, data
    

    def deserialize_bets(self, data):
        deserialize_bets = data.rstrip().split('&')

        bets = []

        for bet in deserialize_bets:
            bets.append(self.__deserialize_bet(bet))
        
        return bets

    
    def deserialize_agency_id(self, data):
        return int(data)
    

    def serialize_amount_response(self, bet_amount, status):
        return f"{BET_HEADER } {status},{bet_amount}\n".encode('utf-8')
    

    
    def serialize_winners(self, winners):
        serialized_winners = ",".join(winners)  # Une los elementos con comas
        return f"{WINNER_HEADER} {serialized_winners}\n".encode('utf-8')
        
    def serialize_not_ready(self):
        return f"{NOT_READY_HEADER} empty\n".encode('utf-8')
