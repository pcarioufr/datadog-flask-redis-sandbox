#!/bin/sh

docker compose \
    -f ./terraform/compose.yml \
    --env-file .env \
    run -it --rm -e "TERM=xterm-256color" \
    terraform ${@}
