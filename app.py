# Import Modules & Create listener
from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import hashlib

app = Flask(__name__)

# Grading Functions
def import_answers(request_ID: int) -> dict:
    with sqlite3.connect('autograder.db') as conn:
        # Check for active lab entry
        entry = pd.read_sql_query(f'SELECT LabID FROM ActiveLabs WHERE RequestID = {request_ID} LIMIT 1', conn)
        if entry.empty:
            return {'error': 'record not found'}
        
        lab = pd.read_sql_query(f'SELECT VerifyAnswerBool FROM LabList WHERE LabID = {entry["LabID"].values[0]} LIMIT 1', conn)
        if lab.empty:
            return {'error': 'no lab found within the database'}
        
        # Check for answer keys
        answers = pd.read_sql_query(f'SELECT * FROM AnswerKey WHERE LabID = {entry["LabID"].values[0]}', conn)
        if answers.empty:
            return {'error': 'no answer keys within the database for this lab'}
        
        # Convert and combine into dictionary
        response = {'LabID': int(entry['LabID'].values[0]), 'VerifyAnswerBool': bool(lab['VerifyAnswerBool'].values[0])}
        response['Values'] = answers.to_dict(orient='records')
        return response
    
    return {'error': 'unknown error'}

# Store grade in database
def submit_answer(submission: dict) -> dict:
    result = {}
    with sqlite3.connect('autograder.db') as conn:
        cursor = conn.cursor()
        # Check for active lab entry
        cursor.execute(f'SELECT LabID FROM ActiveLabs WHERE RequestID = {submission["ID"]} LIMIT 1')
        active_lab = cursor.fetchall()
        if not len(active_lab):
            return {'error': 'record not found'}
        
        # Submit Answers
        cursor.execute(f'INSERT INTO CompletedLabs (RequestID, LabID, SubmissionReceivedBool) VALUES ({submission["ID"]}, {active_lab[0][1]}, 1)')


# Returns True if answer is correct, False if incorrect
def check_key(answer: str, key: str) -> bool: 
    if answer == key:
        return True
    return False

def check_line(answer: str, key: str) -> bool:
    if answer == key:
        return True
    return False

def check_hash(answer: list, key: str, hashed: bool) -> bool:
    if hashed:
        if answer[0] == key:
            return True
        else:
            return False
    
    # Hash answer
    hash = hashlib.sha256()
    for i in answer:
        hash.update(i.encode())
    if hash.hexdigest() == key:
        return True
    return False

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
            if 'hashed' not in list(i.keys()) and i['type'] == 'hash':
                return f'submission/hashed field not provided and required when submission/type equals hash. Position: {iterator}. Aborting.'
            
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

    # Verify number of answers submitted is correct
    if len(data['submission']) == len(AnswerKey['Values']) and AnswerKey['VerifyAnswerBool']:
        for iterator, i in enumerate(data['submission']):
            # Check answer type, then check answer
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
    
    # Submit answer
    #submit_answer(submission=data)
    
    # Calculate grade
    grade = dividend / divisor

    return jsonify({'grade': grade})



# Script running options



# Run Script if launched 
if __name__ == '__main__':
    app.run(debug=True)