#!/bin/bash

if [[ $1 == 'all' ]]; then
    if [[ $2 == '' ]]; then
        version=0.1
    else
        version=$2
    fi
    echo "build mac and linux release of verion ${version}" 
    docker build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../ --push
    docker tag sebalaxi/office-translator:latest sebalaxi/office-translator:${version}
    docker build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/ --push
    docker tag sebalaxi/office-translator-web-app:latest sebalaxi/office-translator-web-app:${version}
else
    echo "build only mac release" 
    docker build -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../
    docker build -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/
fi