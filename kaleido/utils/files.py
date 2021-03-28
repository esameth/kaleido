import json

def load_file(file):
    """Load json file"""
    try:
        return json.load(open(file, 'r+'))
    except:
        return {}

def write_file(file, dict):
    with open(file, 'w+') as f:
        json.dump(dict, f, indent=4)

def exists(search, dict):
    """Check if compound or plate is in the file"""
    return search in dict