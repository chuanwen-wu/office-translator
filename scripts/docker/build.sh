#!/bin/bash

if [[ $1 == 'all' ]]; then
    if [[ $2 == '' ]]; then
        version=0.1
    else
        version=$2
    fi
    echo "build mac and linux release of verion ${version}" 
    docker build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../
    docker push sebalaxi/office-translator:latest
    docker tag sebalaxi/office-translator:latest sebalaxi/office-translator:${version}
    docker push sebalaxi/office-translator:${version}

    docker build --platform linux/amd64,linux/arm64 -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/ --push
    docker push sebalaxi/office-translator-web-app:latest
    docker tag sebalaxi/office-translator-web-app:latest sebalaxi/office-translator-web-app:${version}
    docker push sebalaxi/office-translator-web-app:${version}
else
    echo "build only local release" 
    docker build -t sebalaxi/office-translator:latest -f Dockerfile-controller ../../
    docker build -t sebalaxi/office-translator-web-app:latest -f Dockerfile-web-app ../../web-app/
fi