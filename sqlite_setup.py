import sqlite3
import os
from configparser import ConfigParser
from typing import Optional

def default_config(create_db: Optional[bool] = True, demo_mode: Optional[bool] = False):
    config = ConfigParser()
    db_filepath = 'autograder.db'
    config['general'] = {'db_type': 'SQLite', 'db_filepath': db_filepath, 'demo_mode': demo_mode, 'default_section': 'general'}
    config['grading'] = {'default_weight': 1}
    config['lab'] = {'default_length': 60}

    with open('config.ini', 'w') as file:
        config.write(file)

    if create_db:
        create_db(path=db_filepath, create_samples=demo_mode)

def create_db(path: Optional[str] = '', create_samples: Optional[bool] = False, config_filepath: Optional[str] = 'config.ini', default_weight: Optional[int] = -1, default_length: Optional[int] = -1):
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
                        CreationTime DATETIME,
                        VerifyAnswerBool INTEGER NOT NULL CHECK (VerifyAnswerBool IN (0, 1)),
                        OriginalLab INTEGER,
                        FOREIGN KEY (OriginalLab) REFERENCES LabList(LabID)
                       ); ''')
                       
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS AnswerKey (
                        LabID INTEGER NOT NULL,
                        AnswerID INTEGER NOT NULL,
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
        create_sample_entries()

def create_sample_entries():
    print('sample entries') # Placeholder until sample entries can be developed.

if __name__ == '__main__':
    file = './config.ini'
    if os.path.isfile(file):
        config = ConfigParser()
        config.read(file)
        db_path = config.get('general', 'db_filepath')
        if not os.path.exists(db_path):
            create_db(path=db_path, create_samples=True)
        else:
            print('Database already exists at {db_path}. If you wish to reset it, please delete this file and run the script again.'.format(db_path))
    else:
        default_config(create_db=True, demo_mode=True)
