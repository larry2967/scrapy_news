import yaml

def load_config():
    with open('../docker-compose.yaml', 'r') as stream:
        config = yaml.safe_load(stream)
    return config