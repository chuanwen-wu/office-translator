#! /bin/bash
docker pull apache/kafka
docker run -d -p 9092:9092 --name broker apache/kafka:latest

docker exec --workdir /opt/kafka/bin/ -it broker sh
TOPIC=pptx-translate
GROUP=group1
GROUP2=group2
./kafka-topics.sh --bootstrap-server localhost:9092 --create --topic $TOPIC
# ./kafka-console-producer.sh --bootstrap-server localhost:9092 --topic $TOPIC
# ./kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic $TOPIC --group $GROUP --from-beginning
# ./kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic $TOPIC --group $GROUP --max-messages 1 

TOPIC2=status-update
GROUP2=group2
./kafka-topics.sh --bootstrap-server localhost:9092 --create --topic $TOPIC2
# ./kafka-console-producer.sh --bootstrap-server localhost:9092 --topic $TOPIC2
# ./kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic $TOPIC2 --group $GROUP --from-beginning
# ./kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic $TOPIC2 --group $GROUP --max-messages 1 

docker rm -f broker