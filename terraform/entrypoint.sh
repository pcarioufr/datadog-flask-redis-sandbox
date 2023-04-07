#!/bin/bash

TF_OPTS="-chdir=/opt/box/terraform "

shift $(($OPTIND-1))
CMD=${1}

if [ "$CMD" == "login" ]
then terraform login ; exit 0 
fi

if [ "$CMD" == "output" ]
then echo $(terraform ${TF_OPTS} output -json $@) | jq ; exit 0 
fi

if [ "$CMD" == "init" ]
then terraform ${TF_OPTS} init ; exit 0 
fi

terraform ${TF_OPTS} ${@}
