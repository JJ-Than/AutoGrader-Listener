# Import Modules & Create listener
from flask import Flask, request, jsonify
import pandas as pd
# import sqlite3

app = Flask(__name__)

# Grading Functions
def check_key(value):
    return 'foo'

def check_line(value):
    return 'foo'

def check_file(value):
    return 'foo'

# Create hook functions
@app.route("/", methods=['POST'])
def main():
    data = request.get_json()
    if 'ID' not in data or not isinstance(data['ID'], int):
        return 'ID field not interger or not present. Aborting.'
    if 'Time' not in data or not isinstance(data['Time'], str):
        return 'Time field not string or not present. Aborting.'
    if 'Type' not in data or not isinstance(data['Type'], str):
        return 'Type field not string or not present. Aborting.'
    if 'Submission' not in data or not isinstance(data['Submission'], str):
        return 'Submission field not string or not present. Aborting.'
    
    

# Script running options



# Run Script if launched directly

if __name__ == '__main__':
    app.run(debug=True)