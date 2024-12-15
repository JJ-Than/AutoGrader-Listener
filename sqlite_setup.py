import sqlite3
import os
from configparser import ConfigParser

def default_config():
    config = ConfigParser()
    config['general'] = {'db_type': 'SQLite', 'db_filepath': './autograder.db'}

    with open('config.ini', 'w') as file:
        config.write(file)

def config_reader(keys: list[str]) -> dict:
    config = ConfigParser()
    config.read(file)

    config.default_section = 'general'

def create_db(path: str, create_samples: bool):
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()

        cursor.execute('''

''')

if __name__ == '__main__':
    file = './config.ini'
    if os.path.exists(file) and os.path.isfile(file):
        config = config_reader(['db_path'])
        if os.path.exists(config['db_path']):
