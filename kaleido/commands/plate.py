import re
import sys
import atexit
import string
import logging
import numpy as np
from itertools import product

from kaleido.command import Command
from kaleido.commands.compound import CompoundCommand
from kaleido.utils.files import load_file, write_file, exists

alphabet = list(string.ascii_uppercase)
#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to create a plate                                                          #
#   so that I can keep track of experiments                                                 #
#############################################################################################

class PlateCommand(CompoundCommand):
    """Create a plate containing wells for experiments"""

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('plate_id', type=str, help='Plate ID')
        parser.add_argument('--create', metavar=('width', 'height'),
                            nargs=2, type=int, help='Create a plate with dimensions (width, height)')
        parser.add_argument('--search', action='store_true', help='Search for a plate and get all of its contents')

        # All plates will be stored in a json file with its contents
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called plates.json
        parser.add_argument('--plate_file', default='plates.json',
                            help='File containing plates and their contents')
        # Add compound to a plate
        # Can add multiple compounds - syntax: --add well1=compound, well2=compound
        parser.add_argument('--add', action='append',
                            type=lambda well_comp: well_comp.split('=', 1),
                            dest='add')
        parser.add_argument('--well', type=str, help='Get the compound ID in the well')

    def run(self):
        self.plates = load_file(self._args.plate_file)
        exist = exists(self._args.plate_id, self.plates)
        if exist: self.plate = self.plates[self._args.plate_id]

        if self._args.create:
            if exist:
                sys.exit('Plate already exists')
            self.create_plate()

        elif self._args.search:
            if not exist:
                sys.exit('Plate does not exist\n'
                         'Create the plate by using "kaleidoo plate [plate_id] --create [num rows] [num cols]"')
            display(self.plate)

        elif self._args.add:
            self.add_compound()

        elif self._args.well:
            self.get_compound()

    def create_plate(self):
        width, height = self._args.create[0], self._args.create[1]

        plate = np.full((height, width), '-', dtype=str)
        self.plates[self._args.plate_id] = plate.tolist()
        write_file(self._args.plate_file, self.plates)
        print('Successfully created the plate!')
        display(plate)

    def add_compound(self):
        plate = self.plates[self._args.plate_id]
        # Increment through all added compounds
        for insert in self._args.add:
            well, compound = insert[0], insert[1]
            print(well, compound)
            # Assumption: Cannot add a compound unless it is registered
            # Check to see if the compound is registered first
            print(self.is_registered(compound))

            # Check to see if the well exists

    def get_compound(self):
        # Split well letter (row) and number (column)
        try:
            row, col = re.findall('\d+|\D+', self._args.well)
            # Convert well to location in matrix
            row, col = alphabet.index(row), int(col) - 1
        except:
            sys.exit('Incorrect format: [row letter][col number]')

        # Check if well exists in the plate
        plate = Plate(plate=self.plate)
        print(plate.wells())
        if [row, col] not in plate.avail_wells():
            atexit.register(display, plate=self.plate)
            sys.exit(f"Well does not exist. Available options:\n")


#### User takes contents of a plate.well and puts it into other plate.well
#### Request the contents of a plate.well

class Plate(object):
    def __init__(self, width=None, height=None, plate=None):
        # Matrix that will represent the actual plate
        if plate:
            self.height, self.width = len(plate), len(plate[0])
            self.make_dim()
            self.plate = self.load_plate(plate)
        else:
            self.height, self.width = height, width
            self.make_dim()
            self.plate = self.create_plate()

    def create_plate(self):
        return np.full((self.height, self.width), '-', dtype=str)

    def load_plate(self, plate):
        return np.array(plate)

    # Get well letters and numbers
    def make_dim(self):
        self.side_str = alphabet[:self.height]
        self.well_num = list(map(str, range(1, self.width + 1)))

    # Get all available positions
    def wells(self):
        all = np.array(list(product(list(range(self.height)), list(range(self.width)))))
        print(np.argwhere(self.plate == '-'))
        return list(map(''.join, all))

    def __tolist__(self):
        return self.plate.tolist()

    #def add_comp(self, id):

def display(plate):
    side_str = alphabet[:len(plate)]
    well_num = list(range(1, len(plate[0]) + 1))

    print('\t{}'.format('\t'.join(map(str, well_num))))
    for i in range(len(plate)):
        print('{}\t{}'.format(side_str[i], '\t'.join(plate[i])))