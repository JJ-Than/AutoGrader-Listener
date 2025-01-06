# Import Modules & Create listener
from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import argparse

app = Flask(__name__)

# Grading Functions
def import_answers(request_ID: int) -> dict:
    with sqlite3.connect('autograder.db') as conn:
        # Check for active lab entry
        entry = pd.read_sql_query(f'SELECT LabID FROM ActiveLabs WHERE ID = {request_ID}', conn)
        if entry.empty:
            return {'error': 'record not found'}
        
        lab = pd.read_sql_query(f'SELECT VerifyAnswerBool FROM LabList WHERE ID = {entry["LabID"].values[0]}', conn)
        if lab.empty:
            return {'error': 'no lab found within the database'}
        
        # Check for answer keys
        answers = pd.read_sql_query(f'SELECT * FROM AnswerKey WHERE ID = {entry["LabID"].values[0]}', conn)
        if answers.empty:
            return {'error': 'no answer keys within the database for this lab'}
        
        # Convert and combine into dictionary
        response = {'LabID': int(entry['LabID'].values[0]), 'VerifyAnswerBool': lab['VerifyAnswerBool'].values[0].tobool()}
        response['Values'] = answers.to_dict(orient='records')
        return response

# Returns True if answer is correct, False if incorrect
def check_key(answer, key) -> bool: 
    return True

def check_line(answer, key) -> bool:
    return True

def check_hash(answer, key) -> bool:
    return True

# Create submit hook function
@app.route("/submit", methods=['POST'])
def submit():
    if request.content_type != 'application/json':
        return 'content-type must be set to \'application/json\', and be formatted as a json string. Aborting.'
    
    # Get JSON String
    data = request.get_json()

    # Validate JSON String
    l1_keys = (list(data.keys()))
    if 'id' not in l1_keys or not isinstance(data['ID'], int):
        return 'id field not interger or not present. Aborting.'
    
    if 'time' not in l1_keys or not isinstance(data['Time'], str):
        return 'time field not string or not present. Aborting.'
    
    if 'status' not in l1_keys or not isinstance(data['Type'], int):
        return 'status field not integer or not present. Aborting.'
    elif data['status'] not in [0, 1, 2]:
        return 'status field not valid. Acceptible values: 0, 1, 2. Aborting.'
    
    if 'submission' not in data or not isinstance(data['Submission'], list):
        return 'submission field not list or not present. Aborting.'
    else:
        # Validate submission field for correct format
        for iterator, i in enumerate(data['submission']):
            if not isinstance(i, dict):
                return f'submission field malformed. Position: {iterator}. Aborting.'
            if 'type' not in list(i.keys()):
                return f'submission/type field not provided. Position: {iterator}. Aborting.'
            if i['type'] not in ['key', 'line', 'hash']:
                return f'submission/type field not valid. Position: {iterator}. Aborting.'
            if 'answer' not in list(i.keys()):
                return f'submission/answer field not provided. Position: {iterator}. Aborting.'
            
            # Check for correct variable types
            if i['type'] == 'key' and not isinstance(i['answer'], (int, float, str)):
                return f'submission/answer field has a variable type not compatible with the field submission/type equaling "key". Acceptible variable types: integer, float, string. Position: {iterator}. Aborting.'
            elif i['type'] == 'line' and not isinstance(i['answer'], str):
                return f'submission/answer field has a variable type not compatible with the field submission/type equaling "line". Acceptible variable type: string. Position: {iterator}. Aborting.'
            elif i['type'] == 'hash' and not isinstance(i['answer'], list):
                return f'submission/answer field has a variable type not compatible with the field submission/type equaling "hash". Acceptible variable type: list. Position: {iterator}. Aborting.'
            
    # Import answers
    AnswerKey = import_answers(response_id=data['ID'])

    # Check answers
    dividend = 0
    divisor = 0
    if len(data['submission']) == len(AnswerKey['Values']) and AnswerKey['VerifyAnswerBool']:
        for iterator, i in enumerate(data['submission']):
            if str(i['type']) == 'key' == str(AnswerKey['Values'][iterator]['AnswerType']):
                correct = check_key(i['answer'], AnswerKey['Values'][iterator]['Answer'])
                if correct:
                    dividend += int(AnswerKey['Values'][iterator]['AnswerWeight'])
                divisor += int(AnswerKey['Values'][iterator]['AnswerWeight'])
            elif str(i['type']) == 'line' == str(AnswerKey['Values'][iterator]['AnswerType']):
                correct = check_line(i['answer'], AnswerKey['Values'][iterator]['Answer'])
                if correct:
                    dividend += int(AnswerKey['Values'][iterator]['AnswerWeight'])
                divisor += int(AnswerKey['Values'][iterator]['AnswerWeight'])
            elif str(i['type']) == 'hash' == str(AnswerKey['Values'][iterator]['AnswerType']):
                correct = check_hash(i['answer'], AnswerKey['Values'][iterator]['Answer'])
                if correct:
                    dividend += int(AnswerKey['Values'][iterator]['AnswerWeight'])
                divisor += int(AnswerKey['Values'][iterator]['AnswerWeight'])
            elif str(i['type']) != str(AnswerKey['Values'][iterator]['AnswerType']):
                return f'Incorrect answer type. Position: {iterator}. Aborting.'
            else:
                return f'Error checking answer. Position: {iterator}. Aborting.'
    elif len(data['submission']) != len(AnswerKey['Values']):
        return 'Incorrect number of answers. Aborting.'


# Script running options



# Run Script if launched directly

if __name__ == '__main__':
    app.run(debug=True)