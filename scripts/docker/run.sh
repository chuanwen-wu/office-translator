#!/bin/bash

export MYSQL_ROOT_PASSWORD=a
export DB_USER=root
export DB_PASSWORD=a    

# get host ip
function get_host_ip() {    
    s=$(ifconfig eth0)
    if [ $? -eq 0 ]; then
        host_ip=$(ifconfig eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        echo $host_ip
    else
        s=$(ifconfig en0)
        if [ $? -eq 0 ]; then
            host_ip=$(ifconfig en0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
            echo $host_ip
        else
            echo "no network interface found"
            exit 1
        fi
    fi
}
host_ip=$(get_host_ip)
echo host ip:$host_ip
export host_ip=$host_ip
mkdir -p data/file_repo/done
mkdir -p data/mysql
mkdir -p data/ollama
docker-compose pull
# start docker compose  
docker-compose up -d

# init kafka topic
TOPIC=pptx-translate
docker-compose exec --workdir /opt/kafka/bin/ -it broker \
    ./kafka-configs.sh --bootstrap-server localhost:9092 \
                --alter --entity-type topics \
                --entity-name $TOPIC \
                --add-config max.message.bytes=1048588000
TOPIC2=status-update
docker-compose exec --workdir /opt/kafka/bin/ -it broker \
    ./kafka-configs.sh --bootstrap-server localhost:9092 \
                --alter --entity-type topics \
                --entity-name $TOPIC2 \
                --add-config max.message.bytes=1048588000

# init db
echo "wait 5 seconds for mysql to start..."
sleep 5
echo "init db..."
sql=$(cat db/init.sql)
docker-compose exec -it mysql mysql -u ${DB_USER} -p${DB_PASSWORD} -e "$sql"


# bash ../mq/install.sh

# #host Ip
# EIP=192.168.64.1

# # start controller
# docker run --rm --name controller -p 8080:8080 \
#     -e KAFKA_TOPIC_PPTX=pptx-translate \
#     -e KAFKA_TOPIC_STATUS_UPDATE=status-update \
#     -e KAFKA_SERVERS=${EIP}:9092 \
#     -e DB_HOST=${EIP} \
#     -e DB_USER=root \
#     -e DB_PASSWORD=a \
#     -e DB_NAME=office_translator \
#     -e TZ=Asia/Shanghai \
#     -v $(pwd)/file_repo/:/app/file_repo \
#     -it --entrypoint python sebalaxi/office-translator httpd.py



#  docker run --rm --name worker \
#     -e KAFKA_TOPIC_PPTX=pptx-translate \
#     -e KAFKA_TOPIC_STATUS_UPDATE=status-update \
#     -e KAFKA_SERVERS="${EIP}:9092" \
#     -e OLLAMA_URL=http://${EIP}:11434 \
#     -e TZ=Asia/Shanghai \
#     -it --entrypoint python sebalaxi/office-translator pptx_translator.py