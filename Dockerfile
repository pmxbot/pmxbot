FROM python:3.10-slim

USER root

RUN apt-get -y update; apt-get install -y bash git

RUN mkdir /crunchbot/
COPY . /crunchbot

WORKDIR /crunchbot/

RUN pip install -r requirements.txt
RUN pip install -e .

# These environment variables are required
#export PIVOTAL_TOKEN=
#export MONGO_IP_ADDRESS=
#export MONGO_DATABASE=
#export SLACK_TOKEN=

CMD python crunchbot.py
