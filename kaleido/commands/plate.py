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
    """Perform actions on a plate and its wells"""

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('plate_id', type=str, help='Plate ID')
        # All plates will be stored in a json file with its contents
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called plates.json
        # This file will contain id: {width, height, {filled wells}}
        parser.add_argument('--plate_file', default='plates.json',
                            help='File containing plates and their contents')

        subparsers = parser.add_subparsers(help='Sub-Command Help', dest='which', required=True)

        # All options having to do with a plate
        parser_plate = subparsers.add_parser('plate', help="Search, create, or delete plates")
        parser_plate.set_defaults(which='plate')
        plate_gp = parser_plate.add_mutually_exclusive_group(required=True)
        plate_gp.add_argument('--create', metavar=('width', 'height'),
                            nargs=2, type=int, help='Create a plate with dimensions (width, height)')
        plate_gp.add_argument('--search', action='store_true', help='Search for a plate and get all of its contents')
        plate_gp.add_argument('--delete', action='store_true', help='Remove a plate')


        # All arguments having to do with a well
        parser_well = subparsers.add_parser('well', help="Add, search, or deletes compounds in a well")
        parser_well.set_defaults(which='well')
        well_gp = parser_well.add_mutually_exclusive_group(required=True)
        # Add compound to a plate
        # Can add multiple compounds - syntax: --add well1=compound, well2=compound
        well_gp.add_argument('--add', action='append',
                            type=lambda well_comp: well_comp.split('=', 1),
                            dest='add')
        well_gp.add_argument('--search', type=str, help='Get the compound ID in the well')
        well_gp.add_argument('--delete', type=str, help='Remove contents of a well')

    def run(self):
        self.plates = load_file(self._args.plate_file)
        exist = exists(self._args.plate_id, self.plates)
        if exist:
            self.plate = self.plates[self._args.plate_id]

        which_command = self._args.which
        if which_command == 'plate':
            if self._args.create:
                if exist: sys.exit('Plate already exists')
                self.create_plate()

            elif self._args.search:
                if not exist:
                    sys.exit('Plate does not exist\n'
                             'Create the plate by using "kaleidoo plate [plate_id] --create [num rows] [num cols]"')
                self.search_plate()

            elif self._args.delete:
                if not exist:
                    sys.exit('Plate cannot be deleted because it does not exist')
                self.del_plate()

        else:
            if not exist:
                sys.exit('Plate does not exist\n'
                         'Create the plate by using "kaleidoo plate [plate_id] --create [num rows] [num cols]"')

            if self._args.add:
                self.add_compound()

            elif self._args.search:
                self.get_compound()

            elif self._args.delete:
                self.del_well()

    def create_plate(self):
        # Create a plate
        plate = Plate(self._args.create[0], self._args.create[1])
        self.plates[self._args.plate_id] = plate.__todict__()
        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        print('Successfully created the plate!')
        # Display the empty plate
        display(plate)

    def search_plate(self):
        # Create a plate
        plate = Plate(plate=self.plate)
        print(f'Plate ID:\t{self._args.plate_id}')
        print(f'Num. rows:\t{plate.height}')
        print(f'Num. cols:\t{plate.width}\n')
        display(plate)

    def del_plate(self):
        removed_plate = Plate(plate=self.plates.pop(self._args.plate_id))
        write_file(self._args.plate_file, self.plates)
        print('Successfully removed the plate!')
        print(f'Plate ID:\t{self._args.plate_id}')
        print(f'Num. rows:\t{removed_plate.height}')
        print(f'Num. cols:\t{removed_plate.width}\n')
        if removed_plate.wells:
            display(removed_plate)


    def add_compound(self):
        plate = Plate(plate=self.plate)
        # Increment through all added compounds
        for insert in self._args.add:
            well, compound = insert[0], insert[1]
            print(well, compound)
            # Assumption: Cannot add a compound unless it is registered
            # Check to see if the compound is registered first
            #print(self.is_registered(compound))

            # Check to see if the well exists

    def get_compound(self):
        # Check formatting
        check_well_format(self._args.search)
        # Check if well exists in the plate
        taken_wells = self.plate['plate']
        if self._args.search in taken_wells:
            print(f'Compound {taken_wells[self._args.search]} is in {self._args.plate_id}.{self._args.search}')
        else:
            print(f'There is no compound in {self._args.plate_id}.{self._args.search}')

    def del_well(self):
        # Check formatting
        check_well_format(self._args.delete)
        # Create a plate
        plate = Plate(plate=self.plate)
        if self._args.delete in plate.wells:
            plate.del_well(self._args.delete)
            self.plates[self._args.plate_id]['plate'] = plate.wells
            write_file(self._args.plate_file, self.plates)
            print(f'Successfully removed the contents of {self._args.plate_id}.{self._args.delete}!')
            display(plate)
        else:
            print(f'There is no compound in {self._args.plate_id}.{self._args.delete}')


def check_well_format(well):
    # Split well letter (row) and number (column)
    try:
        row, col = re.findall('\d+|\D+', well)
        # Convert well to location in matrix
        return alphabet.index(row), int(col) - 1
    except:
        sys.exit('Incorrect format: [row letter][col number]')

#### Add compound to plate
#### User takes contents of a plate.well and puts it into other plate.well

class Plate(object):
    def __init__(self, height=None, width=None, plate=None):
        # Matrix that will represent the actual plate
        if plate:
            self.load_plate(plate)
        else:
            self.height, self.width = height, width
            self.create_plate()

    def create_plate(self):
        # Create an empty list to display
        self.wells = {}
        self.plate = np.full((self.height, self.width), '-', dtype=str)

    def load_plate(self, plate):
        self.width = plate['width']
        self.height = plate['height']
        self.wells = plate['plate']
        self.plate = np.full((self.height, self.width), '-', dtype=str)

        for well, comp in self.wells.items():
            row, col = check_well_format(well)
            self.plate[row][col] = comp

    # Get all available positions
    def avail_wells(self):
        all = np.array(list(product(list(range(self.height)), list(range(self.width)))))
        return list(map(''.join, all))

    # Remove a well
    def del_well(self, well):
        self.wells.pop(well)
        row, col = check_well_format(well)
        self.plate[row][col] = '-'

    def __todict__(self):
        return {'width': self.width, 'height': self.height, 'plate': self.wells}

    #def add_comp(self, id):

def display(plate):
    side_str = alphabet[:plate.height]
    well_num = list(range(1, plate.width + 1))

    print('\t{}'.format('\t'.join(map(str, well_num))))
    for i in range(plate.height):
        print('{}\t{}'.format(side_str[i], '\t'.join(plate.plate[i])))