#!/bin/bash

NGINX_VERSION=$1 # script expects NGINX version as parameter
NGINX_MODULES=$(nginx -V 2>&1 | grep "configure arguments" | sed -n 's/.*--modules-path=\([^ ]*\).*/\1/p') 


get_latest_release() {
    curl --silent "https://api.github.com/repos/$1/releases/latest" | jq --raw-output .tag_name
}

get_architecture() {
        case "$(uname -m)" in
        aarch64) echo "arm64" ;;
        arm64) echo "arm64" ;;
        x86_64) echo "amd64" ;;
        amd64) echo "amd64" ;;
        *) echo "" ;;
    esac
}

ARCH=$(get_architecture)

if [ -z "$ARCH" ]; then
    echo 1>&2 "ERROR: Architecture $(uname -m) is not supported."
    exit 1
fi

LIB="ngx_http_datadog_module.so"
TARBALL="ngx_http_datadog_module-${ARCH}-${NGINX_VERSION}.so.tgz"
#TARBALL="nginx_1.26.0-arm64-ngx_http_datadog_module.so.tgz"

RELEASE_TAG=$(get_latest_release DataDog/nginx-datadog)

echo "LIB=${LIB}"
echo "RELEASE_TAG=${RELEASE_TAG}"
echo "TARBALL=${TARBALL}"

curl -Lo ${TARBALL} "https://github.com/DataDog/nginx-datadog/releases/download/${RELEASE_TAG}/${TARBALL}"
tar -xvf ${TARBALL}
mv "${LIB}" "${NGINX_MODULES}/${LIB}"
