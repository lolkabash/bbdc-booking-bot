import sys
import yaml
import logging

# function to load config
def load_config(config_path):
    data = None
    with open(config_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
            sys.exit(1)
    return data
