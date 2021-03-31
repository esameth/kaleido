import sys

from kaleido.plates import Plate
from kaleido.command import Command, FileCommand
from kaleido.utils.util import warning, display, write_file, exists

#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to have a plate                                                            #
#   so that I can keep track of experiments                                                 #
#############################################################################################

class PlateCommand(FileCommand, Command):
    """Create, search/delete a plate or add multiple compounds to a plate"""

    @classmethod
    def init_parser(cls, parser):
        # All arguments having to do with a plate
        parser.add_argument('plate_id', type=str, help='Plate ID')
        plate_gp = parser.add_mutually_exclusive_group(required=True)
        plate_gp.add_argument('--create', metavar=('width', 'height'),
                            nargs=2, type=int, help='Create a plate with dimensions (width, height)')
        plate_gp.add_argument('--search', action='store_true', help='Search for a plate and get all of its contents')
        plate_gp.add_argument('--delete', action='store_true', help='Remove a plate')
        # Add compound to a plate
        # Can add multiple compounds to a single plate - syntax: --add well1=compound --add well2=compound
        # This is useful if you want to populate a single plate
        plate_gp.add_argument('--add', action='append',
                            type=lambda well_comp: well_comp.split('=', 1),
                            dest='add', help="Add compound(s) to well(s) in a plate")

        super(PlateCommand, cls).init_parser(parser)

    def run(self):
        """Run either well or compound command"""
        self.load_file()

        exist = exists(self._args.plate_id, self.plates)
        # If the plate exists, get its contents
        if exist:
            self.plate = Plate(self._args.plate_id, plate=self.plates[self._args.plate_id])
        self.plate_commands(exist)

    def plate_commands(self, exist):
        """Plate commands - create, search, delete, add compounds to plate"""
        # Create a plate if it does not exist already
        if self._args.create:
            if exist: sys.exit('Plate already exists')
            self.create_plate()
        else:
            if not exist:
                warning(f'{self._args.plate_id} does not exist\n'
                        f'Create the plate by using "kaleido plate {self._args.plate_id} --create [num rows] [num cols]"',
                        exit=True)

        if self._args.search:
            self.search_plate()
        elif self._args.delete:
            self.del_plate()
        elif self._args.add:
            self.add_compound()

    def create_plate(self):
        """Create a new plate"""
        # Create a plate
        plate = Plate(self._args.plate_id, self._args.create[0], self._args.create[1])
        self.plates[self._args.plate_id] = plate.__todict__()
        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        print('Successfully created the plate!')
        # Display the empty plate
        display(plate)

    def search_plate(self):
        """Search for a plate and display contents"""
        display(self.plate)

    def del_plate(self):
        """Delete an entire plate"""
        removed_plate = Plate(self._args.plate_id, plate=self.plates.pop(self._args.plate_id))
        write_file(self._args.plate_file, self.plates)
        print('Successfully removed the plate!')
        if removed_plate.wells:
            display(removed_plate)

    def add_compound(self):
        """Add compounds to wells"""
        # Increment through all added compounds
        for insert in self._args.add:
            well, compound = insert[0], insert[1]
            # Check if it is a valid well
            self.plate.check_well_format(well, False)

            # Check if well is already taken
            if well in self.plate.wells:
                warning(f'{well} already has a compound in it and will be skipped.\n'
                        f'To delete the contents of this well use "kaleido well {well} --delete"\n')
                continue
            # Assumption: Cannot add a compound unless it is registered
            # Check to see if the compound is registered first
            exist = exists(compound, self.compounds)
            if not exist or (exist and self.compounds[compound]['state'] == 'stored'):
                warning(f'{compound} is not registered and will be skipped.\n'
                        f'To register this compound use "kaleido compound {compound} --register"\n')
                continue

            self.plate.add_comp(well, compound)
            self.compounds[compound]['plate.well'].append(f'{self.plate._id}.{well}')
            print(f'Successfully added {compound} to {self.plate._id}.{well}\n')

        self.plates[self.plate._id] = self.plate.__todict__()
        # Write the plate to a file
        write_file(self._args.plate_file, self.plates)
        write_file(self._args.comp_file, self.compounds)
        display(self.plate)