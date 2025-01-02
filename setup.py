import os
import json

def load_starting_entries(path: str) -> dict:
    with open(path, 'r') as file:
        return json.load(file)