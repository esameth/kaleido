import re
import sys
import string
import numpy as np
from itertools import product

alphabet = list(string.ascii_uppercase)

class Plate(object):
    """Represents a plate a biologist would create"""
    def __init__(self, height=None, width=None, plate=None):
        if plate:
            self.load_plate(plate)
        else:
            self.height, self.width = height, width
            self.create_plate()

    # Create an empty plate
    def create_plate(self):
        self.wells = {}
        self.plate = np.full((self.height, self.width), '-', dtype=str)

    # Load an already created plate
    def load_plate(self, plate):
        self.width = plate['width']
        self.height = plate['height']
        self.wells = plate['plate']
        self.plate = np.full((self.height, self.width), '-', dtype=str)

        # Populate plate with compounds
        for well, comp in self.wells.items():
            row, col = self.check_well_format(well)
            self.plate[row][col] = comp

    # Remove the contents of a well in a plate
    def del_well(self, well):
        self.wells.pop(well)
        row, col = self.check_well_format(well)
        self.plate[row][col] = '-'

    # Check that the well is in the correct format [letter][num] and it's in a well in the plate
    def check_well_format(self, well):
        # Split well letter (row) and number (column)
        try:
            row, col = re.findall('\d+|\D+', well)
            # Convert well to location in matrix
            row, col = alphabet.index(row), int(col) - 1
        except:
            sys.exit('Incorrect format: [row letter][col number]')
        # Check that it is a well in the plate
        if row >= self.height or col >= self.width:
            sys.exit(f'Well should be a letter up to {alphabet[self.height - 1]} '
                     f'and a number up to {self.width}')
        return row, col

    # Return all of the properties of a plate
    def __todict__(self):
        return {'width': self.width, 'height': self.height, 'plate': self.wells}