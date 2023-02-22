FROM python:3.9.12-alpine3.15
WORKDIR /flask

COPY requirements.txt /flask/build/requirements.txt 
RUN pip3 install --upgrade pip
RUN pip3 install -r build/requirements.txt
