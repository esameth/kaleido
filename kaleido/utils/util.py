import sys
import json
import string
import logging

alphabet = list(string.ascii_uppercase)

def warning(msg, exit=False):
    """Logger warning"""
    logging.warning(msg)
    if exit: sys.exit(1)

def display(plate):
    """Print the plate"""
    print(f'Plate ID:\t{plate._id}')
    print(f'Num. rows:\t{plate.height}')
    print(f'Num. cols:\t{plate.width}\n')

    side_str = alphabet[:plate.height]
    well_num = list(range(1, plate.width + 1))

    print('\t{}'.format('\t'.join(map(str, well_num))))
    for i in range(plate.height):
        print('{}\t{}'.format(side_str[i], '\t'.join(plate.plate[i])))

def write_file(file, dict):
    with open(file, 'w+') as f:
        json.dump(dict, f, indent=4)

def exists(search, dict):
    """Check if compound or plate is in the file"""
    return search in dict