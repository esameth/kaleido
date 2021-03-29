import string
import logging
import numpy as np

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

    def run(self):
        self.plates = load_file(self._args.plate_file)
        exist = exists(self._args.plate_id, self.plates)

        if self._args.create:
            if exist: logging.error('Plate already exists')
            else: self.create_plate()

        elif self._args.search:
            if not exist:
                logging.error('Plate does not exists')
            else: display(self.plates[self._args.plate_id])

        elif self._args.add:
            self.add_compound()

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
            #self.is_registered()

            # Check to see if the well exists


#
# class Plate(object):
#     def __init__(self, id, width=None, height=None, plate=None):
#         self.id = id
#         # Matrix that will represent the actual plate
#         self.plate = self.create_plate(height, width) if not plate else self.load_plate()
#
#     def create_plate(self, height, width):
#         return np.full((height, width), '-', dtype=str)
#
#     def load_plate(self):
#         return
#
#     def __tolist__(self):
#         return self.plate.tolist()
#
#     #def add_comp(self, id):

def display(plate):
    side_str = alphabet[:len(plate)]
    well_num = list(range(1, len(plate[0]) + 1))

    print('\t{}'.format('\t'.join(map(str, well_num))))
    for i in range(len(plate)):
        print('{}\t{}'.format(side_str[i], '\t'.join(plate[i])))