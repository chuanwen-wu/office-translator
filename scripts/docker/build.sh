#!/bin/bash

if [[ $1 == 'all' ]]; then
    echo "build mac and linux release both" 
    docker buildx build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../ --push
    docker buildx build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/ --push
else
    echo "build only mac release" 
    docker build -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../
    docker build -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/
fi