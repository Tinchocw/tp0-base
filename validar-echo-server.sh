
ECHO_SERVER_CONTAINER="sever"
MESSAGE="message-validation"
NET="my-net"


docker network create $NET  # Creo la red por la que me voy a comunicar 
docker network connect $NET server # Conecto el server a la red

RESULT=docker (run --rm -network $NET alpine /bin/sh -c "echo '$MENSAJE' | nc $CONTENEDOR_ECHO_SERVER 12345") # Corro el cliente

if [ "$RESULT" == "$MENSAJE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi


