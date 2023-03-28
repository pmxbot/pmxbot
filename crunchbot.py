import os
from pmxbot.core import initialize, FinalRegistry
from pyaml_env import parse_config

config = parse_config('config.yaml')

if "SLACK_TOKEN" not in os.environ or "MONGO_IP_ADDRESS" not in os.environ or "PIVOTAL_TOKEN" not in os.environ or "MONGO_DATABASE" not in os.environ:
    print("Please set the following environment variables before running this program")
    print("  - MONGO_DATABASE: a valid (production) mongodb database where the datasets are stored so crunchbot can look up dataset information")
    print("  - MONGO_IP_ADDRESS: a valid (production) mongodb ip address so crunchbot can look up dataset information")
    print("  - PIVOTAL_TOKEN: a valid pivotal token so crunchbot can look up pivotal stories")
    print("  - SLACK_TOKEN: a valid slack token so crunchbot can listen for slack posts and make its own slack posts")
    exit(1)

global _bot
_bot = initialize(config)
try:
    _bot.start()
finally:
    FinalRegistry.finalize()
