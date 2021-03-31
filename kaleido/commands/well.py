import sys
import argparse

from kaleido.plates import Plate
from kaleido.command import Command, FileCommand
from kaleido.utils.util import warning, display, write_file, exists

#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to have a plate                                                            #
#   so that I can keep track of experiments                                                 #
#############################################################################################

class WellCommand(FileCommand, Command):
    """Search/delete a well or transfer contents of a well to another plate.well"""

    @classmethod
    def init_parser(cls, parser):
        # All arguments having to do with a well
        parser.add_argument('well_id', type=valid_plate_well, help='Well ID in the format of [Plate].[Well]')
        well_gp = parser.add_mutually_exclusive_group(required=True)
        # User can transfer the contents of a well into different plates/wells
        # Can transfer to multiple plates.wells - syntax: --transfer plate.well1 plate.well2
        well_gp.add_argument('--transfer', type=str, action='append', nargs='+',
                             help='Transfer the contents of the well into other plates')
        well_gp.add_argument('--search', action='store_true', help='Get the compound ID in the well')
        well_gp.add_argument('--delete', action='store_true', help='Remove contents of a well')
        # Add compound to a well
        well_gp.add_argument('--add', type=str, help="Add compound to a well")

        super(WellCommand, cls).init_parser(parser)

    def run(self):
        """Run either well or compound command"""
        self.load_file()

        # Check if the plate exists in the file
        self._args.plate_id, self._args.well = self._args.well_id[0], self._args.well_id[1]

        # If the plate exists, get its contents
        if not exists(self._args.plate_id, self.plates):
            sys.exit('Plate does not exist\n'
                     'Create the plate by using "kaleido plate [plate_id] --create [num rows] [num cols]"')

        self.plate = Plate(self._args.plate_id, plate=self.plates[self._args.plate_id])
        # Validate well
        self.plate.check_well_format(self._args.well)
        self.well_commands()

    def well_commands(self):
        """Well commands - search, delete, transfer contents"""
        # Get the contents of a well
        if self._args.search:
            comp = self.get_compound()
            if comp:
                print(f'Compound {comp} is in {".".join(self._args.well_id)}')
            else:
                print(f'There is no compound in {".".join(self._args.well_id)}')

        elif self._args.delete:
            del_well(self._args.plate_file, self.plates, self.plate, self._args.well)
        elif self._args.transfer:
            self.transfer_well()
        else:
            self.add_compound()

    def get_compound(self):
        """"Return a value in a well"""
        # Check if well exists (and has a compound) in the plate
        taken_wells = self.plate.wells
        if self._args.well in taken_wells:
            return taken_wells[self._args.well]
        return

    def transfer_well(self):
        """Transfer the contents of a well into other plates.wells"""
        # Get the contents of the well
        compound = self.get_compound()
        if not compound:
            sys.exit("There are no contents in that well")
        print("Transferring contents...\n")
        for transfer in self._args.transfer[0]:
            plate, well = valid_plate_well(transfer)
            # Do not add plate if it does not exist
            if not exists(plate, self.plates):
                warning(f'{plate} does not exist\n'
                f'Create the plate by using "kaleido plate {plate} --create [num rows] [num cols]"\n')
                continue

            # Check if well is taken
            plate = Plate(plate, plate=self.plates[plate])
            if well in plate.wells:
                warning(f'{transfer} already has a compound in it and will be skipped.\n'
                f'To delete the contents of this well use "kaleido well {transfer} --delete"\n')
                continue
            # Add well to plate for transfer
            if not plate.add_comp(well, compound):
                continue

            self.compounds[compound]['plate.well'].append(transfer)
            self.plates[plate._id] = plate.__todict__()
            print(f'Successfully added {compound} to {transfer}\n')

        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        write_file(self._args.comp_file, self.compounds)

    def add_compound(self):
        """Add compound to well"""
        # Check if well is already taken
        if self._args.well in self.plate.wells:
            sys.exit(f'{".".join(self._args.well_id)} already has a compound in it.\n'
                    f'To delete the contents of this well use "kaleido well {".".join(self._args.well_id)} --delete"')

        # Assumption: Cannot add a compound unless it is registered
        # Check to see if the compound is registered first
        exist = exists(self._args.add, self.compounds)
        if not exist or (exist and self.compounds[self._args.add]['state'] == 'stored'):
            sys.exit(f'{self._args.add} is not registered.\n'
                    f'To register this compound use "kaleido compound {self._args.add} --register"')

        self.plate.add_comp(self._args.well, self._args.add, True)
        self.compounds[self._args.add]['plate.well'].append(f'{self._args.well_id}')
        print(f'Successfully added {self._args.add} to {".".join(self._args.well_id)}\n')

        self.plates[self.plate._id] = self.plate.__todict__()
        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        write_file(self._args.comp_file, self.compounds)
        display(self.plate)

def valid_plate_well(plate_well):
    """Check that the input is in the format plate.well"""
    # Well ID can only be of length 2: [[plate], [well]]
    value = list(filter(None, plate_well.split('.')))
    if len(value) == 2:
        return value[0], value[1]
    raise argparse.ArgumentTypeError("Well ID must be in the format of [plate].[well]")

def del_well(file, plates, plate, well):
    """Remove the contents of a well"""
    # Check formatting
    plate.check_well_format(well)
    if well in plate.wells:
        plate.del_well(well)
        plates[plate._id]['plate'] = plate.wells
        write_file(file, plates)
        print(f'Successfully removed the contents of {".".join([plate._id, well])}!')
    else:
        print(f'There is no compound in {".".join([plate._id, well])}')