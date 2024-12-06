#!/bin/bash

if [[ $1 == 'all' ]]; then
    echo "build mac and linux release both" 
    docker buildx build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../ --cache-from sebalaxi/office-translator:latest --push
    docker buildx build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/ --cache-from sebalaxi/office-translator-web-app:latest --push
else
    echo "build only mac release" 
    docker build -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../
    docker build -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/
fi