#!/bin/bash
source .secret

if [[ '' == $DB_USER || '' == $MYSQL_ROOT_PASSWORD || '' == $DB_PASSWORD ]]; then
    echo "Env of DB_USER, MYSQL_ROOT_PASSWORD, DB_PASSWORD not found, exit"
    exit 1
fi

os=$(uname)

# get host ip
function get_host_ip() {    
    if [[ 'Darwin' == $os ]]; then
        s=$(ifconfig en0)
        if [ $? -eq 0 ]; then
            host_ip=$(ifconfig en0 | awk '/inet /{print $2}')
            echo $host_ip
        else
            echo "no network interface found"
            exit 1
        fi
    elif [[ 'Linux' == $os ]]; then
        s=$(ifconfig eth0)
        if [ $? -eq 0 ]; then
            host_ip=$(ifconfig eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
            echo $host_ip
        else
            echo "no network interface found"
            exit 1
        fi
    else
        echo "unknown os, failed"
        exit 2
    fi
    return 0
}
if [[ 'Darwin' == $os ]];then
    cp docker-compose-mac.yml docker-compose.yml
    host_ip=$(get_host_ip)
    echo host ip:$host_ip
    export host_ip=$host_ip
elif [[ 'Linux' == $os ]]; then
    cp docker-compose-linux.yml docker-compose.yml
else
    echo "unknown os, failed"
    exit 2
fi

mkdir -p data/file_repo/done
mkdir -p data/file_repo/input
mkdir -p data/mysql
mkdir -p data/ollama

# mac是开发环境，镜像就在本机，无需每次push和pull;
# Linux是测试和生产环境，需要pull最新镜像
if [[ 'Linux' == $os ]]; then
    docker-compose pull
fi
# start docker compose  
docker-compose up broker -d
# sleep 5
# init kafka topic
# TOPIC=pptx-translate
# docker-compose exec --workdir /opt/kafka/bin/ -it broker \
#     ./kafka-configs.sh --bootstrap-server localhost:9092 \
#                 --alter --entity-type topics \
#                 --entity-name $TOPIC \
#                 --add-config max.message.bytes=1048588000
# TOPIC2=status-update
# docker-compose exec --workdir /opt/kafka/bin/ -it broker \
#     ./kafka-configs.sh --bootstrap-server localhost:9092 \
#                 --alter --entity-type topics \
#                 --entity-name $TOPIC2 \
#                 --add-config max.message.bytes=1048588000

docker-compose up mysql -d
# init db
echo "wait 5 seconds for mysql to start..."
sleep 5
echo "init db..."
sql=$(cat db/init.sql)
docker-compose exec -it mysql mysql -u ${DB_USER} -p${DB_PASSWORD} -e "$sql"

if [[ 'Linux' == $os ]]; then
    docker-compose up ollama -d
fi
docker-compose up controller -d
docker-compose up worker -d
docker-compose up web-app -d
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