import sys
import string
import logging
import argparse

from kaleido.plates import Plate
from kaleido.command import Command, FileCommand
from kaleido.commands.compound import CompoundCommand

alphabet = list(string.ascii_uppercase)
#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to have a plate                                                            #
#   so that I can keep track of experiments                                                 #
#############################################################################################

class PlateCommand(FileCommand, Command):
    """Perform actions on a plate and its wells"""

    @classmethod
    def init_parser(cls, parser):
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
        # Can add multiple compounds - syntax: --add well1=compound --add well2=compound
        plate_gp.add_argument('--add', action='append',
                            type=lambda well_comp: well_comp.split('=', 1),
                            dest='add', help="Add compound(s) to well(s) in a plate")


        # All arguments having to do with a well
        parser_well = subparsers.add_parser('well', help="Add, search, or deletes compounds in a well")
        parser_well.set_defaults(which='well')
        parser_well.add_argument('well_id', type=valid_plate_well, help='Well ID in the format of [Plate].[Well]')
        well_gp = parser_well.add_mutually_exclusive_group(required=True)
        # User can transfer the contents of a well into different plates/wells
        # Can transfer to multiple plates.wells - syntax: --transfer plate.well1 plate.well2
        well_gp.add_argument('--transfer', type=str, action='append', nargs='+',
                             help='Transfer the contents of the well into other plates')
        well_gp.add_argument('--search', action='store_true', help='Get the compound ID in the well')
        well_gp.add_argument('--delete', action='store_true', help='Remove contents of a well')

        super(PlateCommand, cls).init_parser(parser)

    def run(self):
        """Run either well or compound command"""
        self.load_file()

        # Check if the plate exists in the file
        if self._args.which == 'well':
            self._args.plate_id, self._args.well = self._args.well_id[0], self._args.well_id[1]

        exist = self.exists(self._args.plate_id, self.plates)
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
        """Plate commands - create, search, delete, add compounds to plate"""
        # Create a plate if it does not exist already
        if self._args.create:
            if exist: sys.exit('Plate already exists')
            self.create_plate()
        else:
            if not exist:
                warning(f'{self._args.id} does not exist\n'
                        f'Create the plate by using "kaleido exp plate {self._args.id} --create [num rows] [num cols]"',
                        exit=True)

        # Retrieve all properties of a plate if it exists
        if self._args.search:
            self.search_plate()

        # Delete a plate if it exists
        elif self._args.delete:
            self.del_plate()

        # Add compounds to the plate at a specified well
        else:
            self.add_compound()


    def well_commands(self):
        """Well commands - search, delete, transfer contents"""
        # Get the contents of a well
        if self._args.search:
            comp = self.get_compound()
            if comp:
                print(f'Compound {comp} is in {".".join(self._args.well_id)}')
            else:
                print(f'There is no compound in {".".join(self._args.well_id)}')

        # Delete the contents of a well
        elif self._args.delete:
            self.del_well()

        # Transfer the contents of a well
        else:
            self.transfer_well()

    def create_plate(self):
        """Create a new plate"""
        # Create a plate
        plate = Plate(self._args.plate_id, self._args.create[0], self._args.create[1])
        self.plates[self._args.plate_id] = plate.__todict__()
        # Write the plate to a file
        self.write_file(self._args.plate_file, self.plates)
        print('Successfully created the plate!')
        # Display the empty plate
        display(plate)

    def search_plate(self):
        """Search for a plate and display contents"""
        display(self.plate)

    def del_plate(self):
        """Delete an entire plate"""
        removed_plate = Plate(self._args.plate_id, plate=self.plates.pop(self._args.plate_id))
        self.write_file(self._args.plate_file, self.plates)
        print('Successfully removed the plate!')
        if removed_plate.wells:
            display(removed_plate)

    def add_compound(self):
        """Add multiple compounds to different wells on a plate"""
        # Increment through all added compounds
        for insert in self._args.add:
            well, compound = insert[0], insert[1]

            # # Check if it is a valid well
            # row, col = self.plate.check_well_format(well)
            # Check if well is already taken
            if well in self.plate.wells:
                warning(f'{well} already has a compound in it and will be skipped.\n'
                f'To delete the contents of this well use "kaleido exp well {well} --delete"\n')
                continue
            # Assumption: Cannot add a compound unless it is registered
            # Check to see if the compound is registered first
            exist = self.exists(compound, self.compounds)
            if not exist or (exist and self.compounds[compound]['state'] == 'stored'):
                warning(f'{compound} is not registered and will be skipped.\n'
                f'To register this compound use "kaleido compound {compound} --register"\n')
                continue

            self.plate.add_comp(well, compound)
            self.compounds[compound]['plate.well'].append(f'{self._args.plate_id}.{well}')
            print(f'Successfully added {compound} to {self._args.plate_id}.{well}\n')

        self.plates[self.plate._id] = self.plate.__todict__()
        # Write the plate to a file
        self.write_file(self._args.plate_file, self.plates)
        self.write_file(self._args.comp_file, self.compounds)
        display(self.plate)

    def get_compound(self):
        """"Return a value in a well"""
        # Check formatting
        self.plate.check_well_format(self._args.well)
        # Check if well exists (and has a compound) in the plate
        taken_wells = self.plate.wells
        if self._args.well in taken_wells:
            return taken_wells[self._args.well]
        return

    def del_well(self):
        """Remove the contents of a well"""
        # Check formatting
        self.plate.check_well_format(self._args.well)
        if self._args.well in self.plate.wells:
            self.plate.del_well(self._args.well)
            self.plates[self._args.plate_id]['plate'] = self.plate.wells
            self.write_file(self._args.plate_file, self.plates)
            print(f'Successfully removed the contents of {".".join(self._args.well_id)}!')
            display(self.plate)
        else:
            print(f'There is no compound in {".".join(self._args.well_id)}')

    def transfer_well(self):
        """Transfer the contents of a well into other plates.wells"""
        # Get the contents of the well
        compound = self.get_compound()
        print("Transferring contents...\n")
        for transfer in self._args.transfer[0]:
            plate, well = valid_plate_well(transfer)
            # Do not add plate if it does not exist
            if not self.exists(plate, self.plates):
                warning(f'{plate} does not exist\n'
                f'Create the plate by using "kaleido exp plate {plate} --create [num rows] [num cols]"\n')
                continue

            # Check if well is valid (empty)
            plate = Plate(plate, plate=self.plates[plate])
            if well in plate.wells:
                warning(f'{transfer} already has a compound in it and will be skipped.\n'
                f'To delete the contents of this well use "kaleido exp well {transfer} --delete"\n')
                continue
            # Add well to plate for transfer
            plate.add_comp(well, compound)
            self.compounds[compound]['plate.well'].append(transfer)
            print(f'Successfully added {compound} to {transfer}\n')
            self.plates[plate._id] = plate.__todict__()

        # Write the plate to a file
        self.write_file(self._args.plate_file, self.plates)
        self.write_file(self._args.comp_file, self.compounds)

def valid_plate_well(plate_well):
    """Check that the input is in the format plate.well"""
    # Well ID can only be of length 2: [[plate], [well]]
    value = list(filter(None, plate_well.split('.')))
    if len(value) == 2:
        return value[0], value[1]
    raise argparse.ArgumentTypeError("Well ID must be in the format of [plate].[well]")

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