import sys
import string
import logging
import argparse

from kaleido.plates import Plate
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

class PlateCommand(Command):
    """Perform actions on a plate and its wells"""

    @classmethod
    def init_parser(cls, parser):
        # All plates will be stored in a json file with its contents
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called plates.json
        # This file will contain id: {width, height, {filled wells}}
        parser.add_argument('--plate_file', default='plates.json',
                            help='File containing plates and their contents')
        # All compounds will be stored in a json file with its state (store or register)
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called compounds.json
        parser.add_argument('--comp_file', default='compounds.json',
                            help='File containing compounds and state (store/register)')

        subparsers = parser.add_subparsers(help='Sub-Command Help', dest='which', required=True)

        # All arguments having to do with a plate
        parser_plate = subparsers.add_parser('plate', help="Search, create, or delete plates")
        parser_plate.set_defaults(which='plate')
        parser_plate.add_argument('plate_id', type=str, help='Plate ID')
        plate_gp = parser_plate.add_mutually_exclusive_group(required=True)
        plate_gp.add_argument('--create', metavar=('width', 'height'),
                            nargs=2, type=int, help='Create a plate with dimensions (width, height)')
        plate_gp.add_argument('--search', action='store_true', help='Search for a plate and get all of its contents')
        plate_gp.add_argument('--delete', action='store_true', help='Remove a plate')
        # Add compound to a plate
        # Can add multiple compounds - syntax: --add well1=compound, well2=compound
        plate_gp.add_argument('--add', action='append',
                            type=lambda well_comp: well_comp.split('=', 1),
                            dest='add')


        # All arguments having to do with a well
        parser_well = subparsers.add_parser('well', help="Add, search, or deletes compounds in a well")
        parser_well.set_defaults(which='well')
        parser_well.add_argument('well_id', type=valid_plate_well, help='Well ID in the format of [Plate].[Well]')
        well_gp = parser_well.add_mutually_exclusive_group(required=True)
        # User can transfer the contents of a well into different plates/wells
        #well_gp.add_argument('--transfer')
        well_gp.add_argument('--search', action='store_true', help='Get the compound ID in the well')
        well_gp.add_argument('--delete', action='store_true', help='Remove contents of a well')

    def run(self):
        self.plates = load_file(self._args.plate_file)
        # Check if the plate exists in the file
        if self._args.which == 'well':
            self._args.plate_id, self._args.well = self._args.well_id[0], self._args.well_id[1]

        exist = exists(self._args.plate_id, self.plates)
        # If the plate exists, get its contents
        if exist:
            self.plate = Plate(self._args.plate_id, plate=self.plates[self._args.plate_id])

        # All commands to do with a well - can only perform this if the plate exists
        if self._args.which == 'well':
            if not exist:
                sys.exit('Plate does not exist\n'
                         'Create the plate by using "kaleido plate [plate_id] --create [num rows] [num cols]"')
            self.well_commands()

        # All commands to do with a plate
        else:
            self.plate_commands(exist)

    def plate_commands(self, exist):
        # Create a plate if it does not exist already
        if self._args.create:
            if exist: sys.exit('Plate already exists')
            self.create_plate()

        # Retrieve all properties of a plate if it exists
        elif self._args.search:
            exist_error(exist)
            self.search_plate()

        # Delete a plate if it exists
        elif self._args.delete:
            exist_error(exist)
            self.del_plate()

        # Add compounds to the plate at a specified well
        else:
            exist_error(exist)
            self.add_compound()


    def well_commands(self):
        # Get the contents of a well
        if self._args.search:
            self.get_compound()

        # Delete the contents of a well
        elif self._args.delete:
            self.del_well()

        else:
            self.compounds = load_file(self._args.comp_file)

    def create_plate(self):
        # Create a plate
        plate = Plate(self._args.plate_id, self._args.create[0], self._args.create[1])
        self.plates[self._args.plate_id] = plate.__todict__()
        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        print('Successfully created the plate!')
        # Display the empty plate
        display(plate)

    def search_plate(self):
        display(self.plate)

    def del_plate(self):
        removed_plate = Plate(self._args.plate_id, plate=self.plates.pop(self._args.plate_id))
        write_file(self._args.plate_file, self.plates)
        print('Successfully removed the plate!')
        if removed_plate.wells:
            display(removed_plate)

    def add_compound(self):
        # Increment through all added compounds
        for insert in self._args.add:
            well, compound = insert[0], insert[1]
            # Check if it is a valid well
            self.plate.check_well_format(well)
            # Check if well is already taken
            if well in self.plate.wells:
                logging.warning(f'{well} already has a compound in it and will be skipped. '
                                f'To delete the contents of this well use:\n'
                                f'kaleido exp well {well} --delete')
                pass
            # Assumption: Cannot add a compound unless it is registered
            # Check to see if the compound is registered first
            exist = exists(compound, self.compounds)
            if not exist or (exist and self.compounds[compound]['state'] == 'stored'):
                logging.warning(f'{compound} is not registered and will be skipped. '
                                f'To register this compound use:\n'
                                f'kaleido compound {compound} --register')
                pass
            

    def get_compound(self):
        # Check formatting
        self.plate.check_well_format(self._args.well)
        # Check if well exists (and has a compound) in the plate
        taken_wells = self.plate.wells
        if self._args.well in taken_wells:
            print(f'Compound {taken_wells[self._args.well]} is in {".".join(self._args.well_id)}')
        else:
            print(f'There is no compound in {".".join(self._args.well_id)}')

    def del_well(self):
        # Check formatting
        self.plate.check_well_format(self._args.well)
        if self._args.well in self.plate.wells:
            self.plate.del_well(self._args.well)
            self.plates[self._args.plate_id]['plate'] = self.plate.wells
            write_file(self._args.plate_file, self.plates)
            print(f'Successfully removed the contents of {".".join(self._args.well_id)}!')
            display(self.plate)
        else:
            print(f'There is no compound in {".".join(self._args.well_id)}')

def valid_plate_well(plate_well):
    # Well ID can only be of length 2: [[plate], [well]]
    value = list(filter(None, plate_well.split('.')))
    if len(value) == 2:
        return value[0], value[1]
    raise argparse.ArgumentTypeError("Well ID must be in the format of [plate].[well]")

def exist_error(exist):
    if not exist:
        sys.exit('Plate does not exist\n'
                 'Create the plate by using "kaleido exp plate [plate_id] --create [num rows] [num cols]"')

def display(plate):
    print(f'Plate ID:\t{plate._id}')
    print(f'Num. rows:\t{plate.height}')
    print(f'Num. cols:\t{plate.width}\n')

    side_str = alphabet[:plate.height]
    well_num = list(range(1, plate.width + 1))

    print('\t{}'.format('\t'.join(map(str, well_num))))
    for i in range(plate.height):
        print('{}\t{}'.format(side_str[i], '\t'.join(plate.plate[i])))

#### Add compound to plate
#### User takes contents of a plate.well and puts it into other plate.well