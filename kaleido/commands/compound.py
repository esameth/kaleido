import sys
import logging
import argparse

from kaleido.command import Command
from kaleido.utils.files import load_file, write_file, exists

#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to input a compound ID                                                     #
#   so that I can store/register a compound                                                 #
#############################################################################################

class CompoundCommand(Command):
    """Store or register a compound, or search for all wells associated with a compound"""

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('id', type=str, help='Compound ID')
        parser.add_argument('--store', action='store_true', help="Store a compound")
        parser.add_argument('--register', action='store_true', help="Register a compound")
        parser.add_argument('--search', action='store_true',
                            help="Search for a compound and its state (stored/registered)")

        # All compounds will be stored in a json file with its state (store or register)
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called compounds.json
        parser.add_argument('--comp_file', default='compounds.json',
                            help='File containing compounds and state (store/register)')

        # A compound can also be assigned to a plate and well
        parser.add_argument('--assign', default=str, metavar=('plate', 'well'), nargs=2,
                            help="Assign the compound to a plate and well")

    def run(self):
        """Run compound command"""
        self.compounds = load_file(self._args.comp_file)

        if self._args.store:
            self.store_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.register:
            self.register_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.search:
            self.search_comp()
        #elif self._args.assign:

    def store_comp(self):
        """Store a compound"""
        # Get state: registered, stored, or does not exist
        registered_state = self.is_registered()

        # Compound does not exist, so store it
        if registered_state is None:
            self.compounds[self._args.id] = {'state': 'stored'}
        # Assumption: once a compound is registered, it can not be unregistered
        elif registered_state:
            logging.error(f'Compound {self._args.id} is already registered and cannot be changed to stored')
        # Give error if compound already stored
        else:
            logging.error(f'Compound {self._args.id} is already stored')

    def register_comp(self):
        """Register a compound"""
        # Get state: registered, stored, or does not exist
        registered_state = self.is_registered()

        # Give error if compound already registered
        if registered_state:
            logging.error(f'Compound {self._args.id} is already registered')
        else:
            self.compounds[self._args.id] = {'state': 'registered', 'plate.well': []}

    def search_comp(self):
        """Search for a compound - gives id, state (stored, registered),
        and all plates.wells associated with it"""
        if self.is_registered() == None:
            print(f'Compound {self._args.id} does not exist')
        else:
            results = self.compounds[self._args.id]
            print(f'id: {self._args.id}')
            print(f'state: {results["state"]}')
            if results["state"] == "registered":
                if results["plate.well"]:
                    print(f'plates: {results["plate.well"]}')

    def is_registered(self):
        """Check state of compound - is it registered already?"""
        # Already stored or registered
        if exists(self._args.id, self.compounds):
            return self.compounds[self._args.id]['state'] == 'registered'
        # Does not exist yet
        return None