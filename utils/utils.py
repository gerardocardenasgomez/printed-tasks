import configparser

def get_config(full_path: str):
    config = configparser.ConfigParser()
    config.read(full_path)
    return config