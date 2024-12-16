import sqlite3
import os
from configparser import ConfigParser

def default_config(create_db: bool, demo_mode: bool):
    config = ConfigParser()
    db_filepath = './autograder.db'
    config['general'] = {'db_type': 'SQLite', 'db_filepath': db_filepath, 'demo_mode': demo_mode}
    config['grading'] = {'default_weight': 1}
    config['lab'] = {'default_length': 60}

    with open('config.ini', 'w') as file:
        config.write(file)

    if create_db == True:
        create_db(db_filepath, demo_mode)

def config_reader(keys: list[str]) -> dict:
    config = ConfigParser()
    config.read(file)

    config.default_section = 'general'

    

def create_db(path: str, create_samples: bool):
    config = config_reader(['grading/default_weight', 'lab/default_length']) # TODO Allow different section parsing of config file with forward slash '/'
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXIST LabList (
                        LabID INTEGER PRIMARY KEY,
                        LabName TEXT NOT NULL,
                        CreationTime DATETIME,
                        VerifyAnswerBool INTEGER NOT NULL CHECK (VerifyAnswer IN (0, 1)),
                        OriginalLab INTEGER,
                        FOREIGN KEY (OriginalLab) REFERENCES LabList(LabID)
                       );
                       
            CREATE TABLE IF NOT EXIST AnswerKey (
                        LabID INTEGER NOT NULL,
                        AnswerID INTEGER NOT NULL,
                        AnswerType TEXT NOT NULL CHECK (LabType IN ('Key', 'Line', 'Hash')),
                        AnswerWeight INTEGER NOT NULL DEFAULT {default_weight},
                        Answer TEXT NOT NULL,
                        PRIMARY KEY (LabID, AnswerID),
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       );
                       
            CREATE TABLE IF NOT EXIST ActiveLabs (
                        RequestID INTEGER PRIMARY KEY,
                        LabID INTEGER NOT NULL,
                        DeploymentTime DATETIME NOT NULL,
                        TimeLimit INTEGER NOT NULL DEFAULT {default_length},
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       );
                       
            CREATE TABLE IF NOT EXIST CompleteLabs (
                        RequestID INTEGER PRIMARY KEY,
                        LabID INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        DeploymentTime DATETIME NOT NULL,
                        TimeLimit INTEGER NOT NULL,
                        CompletionTime DATETIME NOT NULL,
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       );
                       
            CREATE TABLE IF NOT EXIST SubmittedAnswers (
                        RequestID INTEGER NOT NULL,
                        SubmittedAnswer INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        Submission TEXT NOT NULL,
                        PRIMARY KEY (RequestID, SubmittedAnswer),
                        FOREIGN KEY (RequestID) REFERENCES CompletedLabs(RequestID)
                       ); '''
        ).format(default_weight=config['default_weight'], default_config=config['default_config'])

        conn.commit()

if __name__ == '__main__':
    file = './config.ini'
    if os.path.exists(file) and os.path.isfile(file):
        config = config_reader(['db_path'])
        if not os.path.exists(config['db_path']):
            create_db(path=config['db_path'], create_samples=True)
        else:
            print('Database already exists at {db_path}. If you wish to reset it, please delete this file and run the script again.'.format(config['db_path']))
    else:
        default_config(create_db=True, demo_mode=True)
