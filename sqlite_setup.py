# Importing Libraries
import sqlite3
import os
import re
import argparse
from configparser import ConfigParser
from typing import Optional
import pandas as pd

# Importing Functions from project <scripts>.py
from setup import load_starting_entries


# Per Google's recommendation, creating the main function for the Argparser
def main():
    # Input argument reading
    parser = argparse.ArgumentParser(description='Create a SQLite database for the autograder.', add_help=True)
    parser.add_argument('-c', '--config', '--config-filepath', help='Path to the config file.', type=str, default='config.ini')
    parser.add_argument('-d', '--database-filepath', '--db', help='Path to the database file.', type=str, default='autograder.db')
    parser.add_argument('-D', '--demo-mode', help='Create a demo database (same as -i ./demo-files/demo-entries.json).\nNo effect if specifying a config file.', action='store_true', default=False)
    parser.add_argument('-f', '--force', help='Attempts to force the command to go through by performing limited error-correction. Does not prevent all errors from occurring.', action='store_true', default=False)
    #parser.add_argument('-i', '--input-file', help='Path to the input file for the demo database.', type=str)
    parser.add_argument('-w', '--default-weight', help='Default weight for each answers. Set to 1 if not specified.', type=int, default=1)

    # Default length for the student to complete the lab after it is triggered
    parser_length = parser.add_mutually_exclusive_group(required=False)
    parser_length.add_argument('-l', '--default-length', help='Default length for the student to complete the lab after it is triggered. Default is 60 minutes.\nInput number followed by time unit. EX: 30m, 1h, 3d', type=str)
    parser_length.add_argument('--default-length-minutes', help='Default length for the student to complete the lab after it is triggered in minutes', type=int)
    parser_length.add_argument('--default-length-hours', help='Default length for the student to complete the lab after it is triggered in hours', type=int)
    parser_length.add_argument('--default-length-days', help='Default length for the student to complete the lab after it is triggered in days', type=int)
    parser_length.add_argument('--default-length-weeks', help='Default length for the student to complete the lab after it is triggered in weeks', type=int)

    # Specify Verbosity (verbose = 1 is default)
    parser_verbosity = parser.add_mutually_exclusive_group(required=False)
    parser_verbosity.add_argument('-q', '--quiet', help='Set output to quiet. Will suppress all outputs.', action='store_true', default=False) # Verbose = 0
    parser_verbosity.add_argument('-v', '--verbose', help='Set output to verbose.', action='store_true', default=False) # Verbose = 2
    parser_verbosity.add_argument('-vv', '--very-verbose', help='Set output to very verbose.', action='store_true', default=False) # Verbose = 3

    # Parse the arguments
    args = parser.parse_args()

    # set verbosity level
    if args.quiet:
        verbose = 0
    elif args.verbose:
        verbose = 2
    elif args.very_verbose:
        verbose = 3
    else:
        verbose = 1

    # get default length
    try:
        if args.default_length:
            if 'm' == args.default_length[-1] and args.default_length[:-1].isdigit():
                default_length = int(args.default_length[:-1])
            elif 'h' == args.default_length[-1] and args.default_length[:-1].isdigit():
                default_length = int(args.default_length[:-1]) * 60
            elif 'd' == args.default_length[-1] and args.default_length[:-1].isdigit():
                default_length = int(args.default_length[:-1]) * 1440
            elif 'w' == args.default_length[-1] and args.default_length[:-1].isdigit():
                default_length = int(args.default_length[:-1]) * 10080
            else:
                raise ValueError(f'malformed value: {args.default_length}. Please use a number followed by a supported time unit (m, h, d, w). EX: 30m, 1h, 3d.')
        elif args.default_length_minutes:
            default_length = args.default_length_minutes
        elif args.default_length_hours:
            default_length = args.default_length_hours * 60
        elif args.default_length_days:
            default_length = args.default_length_days * 1440
        elif args.default_length_weeks:
            default_length = args.default_length_weeks * 10080
        else:
            default_length = 60

    except ValueError as e:
        if verbose:
            print(e)
        
        if args.force and verbose:
            print('Forcing the command to go through. Default length set to 60 minutes.')
            default_length = 60
        elif args.force:
            default_length = 60
        else:
            exit

    except Exception as e:
        if verbose:
            print(e)
        exit

    #if verbose >= 3:
    #    print(f'Verbosity: {verbose}\nDefault Length: {default_length}')

    # chooses which function(s) to run
    file = args.config
    if os.path.isfile(file):
        config = ConfigParser()
        config.read(file)
        db_path = config.get('general', 'db_filepath')

        # Sets Demo Mode based on config file
        demo_mode = bool(config.getboolean('general', 'demo_mode'))

        if db_path == args.database_filepath == 'autograder.db' and not os.path.isfile(args.database_filepath) or db_path != args.database_filepath and not os.path.isfile(args.database_filepath):
            if verbose >= 2:
                print(f'Creating database at: {args.database_filepath}\nUsing database_filepath from input arguments.')
            func_create_db(path=args.database_filepath, create_samples=demo_mode, config_filepath=file, default_weight=args.default_weight, default_length=default_length, verbose=verbose)

        elif db_path == args.database_filepath and not os.path.isfile(db_path):
            if verbose >= 2:
                print(f'Creating database at: {db_path}\nUsing database_filepath from config file.')
            func_create_db(path=db_path, create_samples=demo_mode, config_filepath=file, default_weight=args.default_weight, default_length=default_length, verbose=verbose)
            
        elif os.path.isfile(db_path) or os.path.isfile(args.database_filepath):
            if verbose and db_path == args.database_filepath:
                print(f'Database already exists at {db_path}. If you wish to reset it, please delete this file and run the script again.')
            elif verbose:
                print(f'Database already exists at {db_path} and {args.database_filepath}. If you wish to reset it, please delete one of these files and run the script again.')
    else:
        if verbose >= 2:
            print(f'Creating config file at: {file}')
        default_config(create_db=True, demo_mode=args.demo_mode, db_filepath=args.database_filepath, config_filepath=file, default_length=default_length, default_weight=args.default_weight, verbose=verbose)


# Create a default config file
def default_config(create_db: Optional[bool] = True, demo_mode: Optional[bool] = False, db_filepath: Optional[str] = 'autograder.db', config_filepath: Optional[str] = 'config.ini', default_length: Optional[int] = 60, default_weight: Optional[int] = 1, verbose: Optional[int] = 1):
    config = ConfigParser()
    config['general'] = {'db_type': 'SQLite', 'db_filepath': db_filepath, 'demo_mode': demo_mode, 'default_section': 'general'}
    config['grading'] = {'default_weight': default_weight}
    config['lab'] = {'default_length': default_length}

    with open(config_filepath, 'w') as file:
        config.write(file)

    if create_db:
        func_create_db(path=db_filepath, create_samples=demo_mode, config_filepath=config_filepath, default_length=default_length, default_weight=default_weight, verbose=verbose)


# Create the database tables
def func_create_db(path: Optional[str] = '', create_samples: Optional[bool] = False, config_filepath: Optional[str] = 'config.ini', default_weight: Optional[int] = -1, default_length: Optional[int] = -1, verbose: Optional[int] = 1):
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

    if verbose >= 2:
        print(f'Creating database at: {path}\n')
    with sqlite3.connect(path) as conn:
        table_list = ['''
            CREATE TABLE IF NOT EXISTS LabList (
                        LabID INTEGER PRIMARY KEY,
                        LabName TEXT NOT NULL,
                        VerifyAnswerBool INTEGER NOT NULL CHECK (VerifyAnswerBool IN (0, 1)),
                        OriginalLab INTEGER,
                        CreationTime DATETIME,
                        FOREIGN KEY (OriginalLab) REFERENCES LabList(LabID)
                       ); ''', 
                       f'''
            CREATE TABLE IF NOT EXISTS AnswerKey (
                        LabID INTEGER NOT NULL,
                        AnswerID INTEGER NOT NULL,
                        AnswerName TEXT NOT NULL,
                        AnswerType TEXT NOT NULL CHECK (AnswerType IN ('Key', 'Line', 'Hash')),
                        AnswerWeight INTEGER NOT NULL DEFAULT {default_weight},
                        Answer TEXT NOT NULL,
                        PRIMARY KEY (LabID, AnswerID),
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''', 
                       f'''
            CREATE TABLE IF NOT EXISTS ActiveLabs (
                        RequestID INTEGER PRIMARY KEY,
                        LabID INTEGER NOT NULL,
                        DeploymentTime DATETIME,
                        TimeLimit INTEGER NOT NULL DEFAULT {default_length},
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''', 
                       '''
            CREATE TABLE IF NOT EXISTS CompleteLabs (
                        RequestID INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        LabID INTEGER NOT NULL,
                        DeploymentTime DATETIME,
                        TimeLimit INTEGER,
                        CompletionTime DATETIME,
                        SubmissionReceivedBool INTEGER NOT NULL DEFAULT 1 CHECK (SubmissionReceivedBool IN (0, 1)),
                        PRIMARY KEY (RequestID, SubmissionID),
                        FOREIGN KEY (LabID) REFERENCES LabList(LabID)
                       ); ''',
                       '''
            CREATE TABLE IF NOT EXISTS SubmittedAnswers (
                        RequestID INTEGER NOT NULL,
                        SubmissionID INTEGER NOT NULL,
                        AnswerID INTEGER NOT NULL,
                        Submission TEXT NOT NULL,
                        PRIMARY KEY (RequestID, SubmissionID, AnswerID),
                        FOREIGN KEY (RequestID) REFERENCES CompleteLabs(RequestID)
                       ); ''']

        cursor = conn.cursor()

        for table in table_list:
            if verbose >= 3:
                print(f'Creating table with command:\n{table}\n')
            cursor.execute(table)

        conn.commit()

    if create_samples:
        if verbose >= 3:
            print('Creating demo database entries.')
        entries = load_starting_entries('demo-files/demo-entries.json')
        # print(entries)
        create_starting_entries(path=path, entries=entries, verbose=verbose)


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
            if verbose >= 2:
                print(f'Entry added to {data["table"]}\n{entry}\n--------------------')
        conn.commit()

        # Show committed entries
        if verbose >= 2:
            cursor.execute('SELECT * FROM LabList')
            df_LabList = pd.DataFrame.from_dict(cursor.fetchall())
            if not df_LabList.empty:
                df_LabList.columns = ['LabID', 'LabName', 'VerifyAnswerBool', 'OriginalLab', 'CreationTime']
                print(f'LabList Table:\n{df_LabList.to_string(index=False)}\n')

            cursor.execute('SELECT * FROM AnswerKey')
            df_AnswerKey = pd.DataFrame.from_dict(cursor.fetchall())
            if not df_AnswerKey.empty:
                df_AnswerKey.columns = ['LabID', 'AnswerID', 'AnswerName', 'AnswerType', 'AnswerWeight', 'Answer']
                print(f'AnswerKey Table:\n{df_AnswerKey.to_string(index=False)}\n')

            cursor.execute('SELECT * FROM ActiveLabs')
            df_ActiveLabs = pd.DataFrame.from_dict(cursor.fetchall())
            if not df_ActiveLabs.empty:
                df_ActiveLabs.columns = ['RequestID', 'SubmissionID', 'LabID', 'DeploymentTime', 'TimeLimit', 'SubmissionReceivedBool']
                print(f'ActiveLabs Table:\n{df_ActiveLabs.to_string(index=False)}\n')

            cursor.execute('SELECT * FROM CompleteLabs')
            df_CompletedLabs = pd.DataFrame.from_dict(cursor.fetchall())
            if not df_CompletedLabs.empty:
                df_CompletedLabs.columns = ['RequestID', 'SubmissionID', 'LabID', 'DeploymentTime', 'TimeLimit', 'CompletionTime', 'SubmissionReceivedBool']
                print(f'CompletedLabs Table:\n{df_CompletedLabs.to_string(index=False)}\n')

            cursor.execute('SELECT * FROM SubmittedAnswers')
            df_SubmittedAnswers = pd.DataFrame.from_dict(cursor.fetchall())
            if not df_SubmittedAnswers.empty:
                df_SubmittedAnswers.columns = ['RequestID', 'SubmissionID', 'AnswerID', 'Submission']
                print(f'SubmittedAnswers Table:\n{df_SubmittedAnswers.to_string(index=False)}\n')

if __name__ == '__main__':
    main()