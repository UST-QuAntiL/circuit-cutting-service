FROM python:3.9.0-slim-buster

WORKDIR /circuit-cutting-service
COPY . /circuit-cutting-service

RUN pip3 install -r requirements.txt 

ENTRYPOINT [ "python" ]

CMD ["circuit-cutting-service.py" ]