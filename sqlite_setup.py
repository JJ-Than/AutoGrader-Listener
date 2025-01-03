import sqlite3
import os
from configparser import ConfigParser
from typing import Optional
from setup import load_starting_entries
import re

# Create a default config file
def default_config(create_db: Optional[bool] = True, demo_mode: Optional[bool] = False):
    config = ConfigParser()
    db_filepath = 'autograder.db'
    config['general'] = {'db_type': 'SQLite', 'db_filepath': db_filepath, 'demo_mode': demo_mode, 'default_section': 'general'}
    config['grading'] = {'default_weight': 1}
    config['lab'] = {'default_length': 60}

    with open('config.ini', 'w') as file:
        config.write(file)

    if create_db:
        func_create_db(path=db_filepath, create_samples=demo_mode)

# Create the database tables
def func_create_db(path: Optional[str] = '', create_samples: Optional[bool] = False, config_filepath: Optional[str] = 'config.ini', default_weight: Optional[int] = -1, default_length: Optional[int] = -1):
    if not os.path.isfile(config_filepath): # IF config doesn't exist AND \
        if path == '' or default_weight >= -1 or default_length >= -1: # IF all required parameters are not defined \
            # Error out
            print('Config file could not be found, and all required parameters are not defined in the it\'s place. Please either provide a config file, or provide the "default_weight, default_length, and path" parameters.') 
            exit
    else:                                           #IF config exists AND \
        if path == '' or default_weight >= -1 or default_length >= -1: # IF all required parameters are not defined \
            # Import config file
            config = ConfigParser()
            config.read(config_filepath)
    if default_weight == -1 and default_length == -1:
        default_weight = config.get('grading', 'default_weight')
        default_length = config.get('lab', 'default_length')
    elif default_weight == -1:
        default_weight = config.get('grading', 'default_weight')
    elif default_length == -1:
        default_length = config.get('lab', 'default_length')


    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LabList (
                        LabID INTEGER PRIMARY KEY,
                        LabName TEXT NOT NULL,
                        VerifyAnswerBool INTEGER NOT NULL CHECK (VerifyAnswerBool IN (0, 1)),
                        OriginalLab INTEGER,
                        CreationTime DATETIME,
                        FOREIGN KEY (OriginalLab) REFERENCES LabList(LabID)
                       ); ''')
                       
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS AnswerKey (
                        LabID INTEGER NOT NULL,
                        AnswerID INTEGER NOT NULL,
                        AnswerName TEXT NOT NULL,
                        AnswerType TEXT NOT NULL CHECK (AnswerType IN ('Key', 'Line', 'Hash')),
                        AnswerWeight INTEGER NOT NULL DEFAULT {default_weight},
                        Answer TEXT NOT NULL,
                        PRIMARY KEY (LabID, AnswerID),
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''')
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS ActiveLabs (
                        RequestID INTEGER PRIMARY KEY,
                        LabID INTEGER NOT NULL,
                        DeploymentTime DATETIME NOT NULL,
                        TimeLimit INTEGER NOT NULL DEFAULT {default_length},
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CompleteLabs (
                        RequestID INTEGER PRIMARY KEY,
                        LabID INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        DeploymentTime DATETIME NOT NULL,
                        TimeLimit INTEGER NOT NULL,
                        CompletionTime DATETIME NOT NULL,
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''')
                       
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SubmittedAnswers (
                        RequestID INTEGER NOT NULL,
                        SubmittedAnswer INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        Submission TEXT NOT NULL,
                        PRIMARY KEY (RequestID, SubmittedAnswer),
                        FOREIGN KEY (RequestID) REFERENCES CompletedLabs(RequestID)
                       ); ''')

        conn.commit()

    if create_samples:
        entries = load_starting_entries('demo-files/demo-entries.json')
        # print(entries)
        create_starting_entries(path=path, entries=entries, verbose=2)

# Takes in list of entries to add to the database
def create_starting_entries(path: str, entries: dict, verbose: Optional[int] = 1):
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        re_pattern = re.escape('\'')

        for data in entries["data"]:
            keys = ', '.join(list(data["values"].keys()))
            keys = re.sub(re_pattern, '', keys)

            values = []
            for value in data["values"].values():
                if str(value).isdigit():
                    values.append(value)
                else:
                    values.append(f'"{value}"')
            values = ', '.join(str(value) for value in values)

            entry = f'INSERT INTO {data["table"]} ({keys}) VALUES ({values});'
            cursor.execute(entry)
            if verbose:
                print(f'Entry added to {data["table"]}\n{entry}\n--------------------')
        conn.commit()

        # Show committed entries
        if verbose >= 2:
            cursor.execute('SELECT * FROM LabList')
            print(f'LabList Table:\n{cursor.fetchall()}\n')
            cursor.execute('SELECT * FROM AnswerKey')
            print(f'AnswerKey Table:\n{cursor.fetchall()}\n')
            cursor.execute('SELECT * FROM ActiveLabs')
            print(f'ActiveLabs Table:\n{cursor.fetchall()}\n')
            cursor.execute('SELECT * FROM CompleteLabs')
            print(f'CompletedLabs Table:\n{cursor.fetchall()}\n')
            cursor.execute('SELECT * FROM SubmittedAnswers')
            print(f'SubmittedAnswers Table:\n{cursor.fetchall()}\n')

if __name__ == '__main__':
    file = './config.ini'
    if os.path.isfile(file):
        config = ConfigParser()
        config.read(file)
        db_path = config.get('general', 'db_filepath')
        if not os.path.exists(db_path):
            func_create_db(path=db_path, create_samples=True)
        else:
            print(f'Database already exists at {db_path}. If you wish to reset it, please delete this file and run the script again.')
    else:
        default_config(create_db=True, demo_mode=True)