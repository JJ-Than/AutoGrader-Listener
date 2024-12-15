# Import Modules & Create listener
from flask import Flask, request, jsonify
import pandas as pd
# import sqlite3

app = Flask(__name__)

# Create hook functions
@app.route("/", methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        data = request.get_json()
        return 'WOOHOO!!!'

# Script running options



# Run Script if launched directly

if __name__ == '__main__':
    app.run(debug=True)