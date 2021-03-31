import re
import sys
import string
import logging
import numpy as np
from itertools import product

from kaleido.utils.util import warning

alphabet = list(string.ascii_uppercase)

class Plate(object):
    """Represents a plate a biologist would create"""
    def __init__(self, id, height=None, width=None, plate=None):
        self._id = id
        if plate:
            self.load_plate(plate)
        else:
            self.height, self.width = height, width
            self.create_plate()

    def create_plate(self):
        """Create an empty plate"""
        self.wells = {}
        self.plate = np.full((self.height, self.width), '-', dtype=str)

    def load_plate(self, plate):
        """Load an already created plate"""
        self.width = plate['width']
        self.height = plate['height']
        self.wells = plate['plate']
        self.plate = np.full((self.height, self.width), '-', dtype=str)

        # Populate plate with compounds
        for well, comp in self.wells.items():
            row, col, OK = self.check_well_format(well)
            self.plate[row][col] = comp

    def del_well(self, well):
        """Remove the contents of a well in a plate"""
        self.wells.pop(well)
        row, col = self.check_well_format(well)
        self.plate[row][col] = '-'

    def check_well_format(self, well, exit=True):
        """Check that the well is in the correct format [letter][num] and it's in a well in the plate"""
        # Split well letter (row) and number (column)
        OK = True
        try:
            row, col = re.findall('\d+|\D+', well)
            # Convert well to location in matrix
            row, col = alphabet.index(row), int(col) - 1
        except:
            warning(f'{well} is in the incorrect format.\n'
                    f'Correct format: [row letter][col number]', exit)
            OK = False
        # Check that it is a well in the plate
        if row >= self.height or col >= self.width:
            warning(f'{well} should be a letter up to {alphabet[self.height - 1]} '
                    f'and a number up to {self.width}', exit)
            OK = False
        return row, col, OK

    def add_comp(self, well, comp, exit=False):
        """Add compound to position"""
        row, col, OK = self.check_well_format(well, exit)
        if OK:
            self.plate[row][col] = comp
            self.wells[well] = comp
            return True
        return False

    # Return all of the properties of a plate
    def __todict__(self):
        return {'width': self.width, 'height': self.height, 'plate': self.wells}