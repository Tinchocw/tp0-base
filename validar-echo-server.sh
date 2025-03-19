
ECHO_SERVER_CONTAINER="server"
MESSAGE="message-validation"
NET="tp0_testing_net"

RESULT=$(docker run --rm --network $NET  alpine /bin/sh -c "echo '$MESSAGE' | nc $ECHO_SERVER_CONTAINER 12345")

if [ "$RESULT" == "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi


