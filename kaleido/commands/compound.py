import sys

from kaleido.plates import Plate
from kaleido.compounds import Compound
from kaleido.commands.well import del_well, valid_plate_well
from kaleido.command import Command, FileCommand
from kaleido.utils.util import write_file, exists

#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to input a compound ID                                                     #
#   so that I can store/register a compound                                                 #
#############################################################################################

class CompoundCommand(FileCommand, Command):
    """Store/register a compound, or search/delete all plate.wells associated with a compound"""

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('id', type=str, help='Compound ID')
        parser.add_argument('--store', action='store_true', help="Store a compound")
        parser.add_argument('--register', action='store_true', help="Register a compound")
        parser.add_argument('--search', action='store_true',
                            help="Search for a compound, its state (stored/registered), and all plates it is in")
        parser.add_argument('--delete', action='store_true', help='Remove a compound')

        super(CompoundCommand, cls).init_parser(parser)

    def run(self):
        """Run compound command"""
        self.load_file()
        self.comp = self.load_comp()

        if self._args.store:
            self.store_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.register:
            self.register_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.search:
            self.search_comp()
        else:
            self.delete_comp()

    def store_comp(self):
        """Store a compound"""
        # Already stored or registered
        if not self.comp:
            self.compounds[self._args.id] = Compound(self._args.id, state='stored').__todict__()
        else:
            # Assumption: once a compound is registered, it can not be unregistered
            if self.comp.state == 'registered':
                sys.exit(f'Compound {self.comp._id} is already registered and cannot be changed to stored')
            # Give error if compound already stored
            else:
                sys.exit(f'Compound {self.comp._id} is already stored')
        print(f'Successfully stored {self._args.id}')

    def register_comp(self):
        """Register a compound"""
        # Give error if compound already registered
        if self.comp and self.comp.state == 'registered':
            sys.exit(f'Compound {self.comp._id} is already registered')
        else:
            self.compounds[self._args.id] = Compound(self._args.id, state='registered').__todict__()
        print(f'Successfully registered {self._args.id}')

    def search_comp(self):
        """Search for a compound - gives id, state (stored, registered),
        and all plates.wells associated with it"""
        if not self.comp:
            print(f'Compound {self._args.id} does not exist')
        else:
            print(f'Compound id: {self.comp._id}')
            print(f'State: {self.comp.state}\n')
            if self.comp.plate:
                print('Associated plates and wells: \n{}'.format('\n'.join(self.comp.plate)))

    def delete_comp(self):
        """Delete a compound if it exists"""
        # Give error if the compound does not exist
        if not self.comp:
            sys.exit(f'Compound {self._args.id} does not exist')

        # Remove the plate.well the compound is in
        for remove in self.comp.plate:
            plate, well = valid_plate_well(remove)
            del_well(self._args.plate_file, self.plates, Plate(plate, plate=self.plates[plate]), well)
        # Remove from compound file
        del self.compounds[self.comp._id]
        write_file(self._args.comp_file, self.compounds)
        print(f'Successfully deleted {self._args.id}')

    def load_comp(self):
        # Already stored or registered
        if exists(self._args.id, self.compounds):
            return Compound(self._args.id, props=self.compounds[self._args.id])