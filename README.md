# Crunchbot

Crunchbot is defined as 3rd party library pmxbot with all the standard functionality (e.g. pmxbot handlers) it has + 2
pieces of custom functionality specific to Crunch:

1. Look up and post dataset and folder information when user types in `!ds`.
2. Look up and post pivotal ticket information when a pivotal story id is detected in text.

## Install locally
```bash
pip install -r requirements.txt
pip install -e .
```

## Run locally
```bash
# These environment variables are required
export PIVOTAL_TOKEN=
export MONGO_IP_ADDRESS=
export MONGO_DATABASE=
export SLACK_TOKEN=

python crunchbot.py
```

## Run in docker
```bash
docker build . -t crunchbot

docker run crunchbot

Please set the following environment variables before running this program
  - MONGO_DATABASE: a valid (production) mongodb database where the datasets are stored so crunchbot can look up dataset information
  - MONGO_IP_ADDRESS: a valid (production) mongodb ip address so crunchbot can look up dataset information
  - PIVOTAL_TOKEN: a valid pivotal token so crunchbot can look up pivotal stories
  - SLACK_TOKEN: a valid slack token so crunchbot can listen for slack posts and make its own slack posts

docker run -e "MONGO_DATABASE=io_crunch_db" -e "MONGO_IP_ADDRESS=" -e "PIVOTAL_TOKEN=" -e "SLACK_TOKEN=" crunchbot

```