import json
import logging
import argparse

from kaleido.command import Command

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
        parser.add_argument('action', choices=['store', 'register', 'search'],
                            help='Compound action')

        # All compounds will be stored in a json file with its state (store or register)
        # If a file was given, load it
        # Otherwise, read or create the default file which we assume will be called compounds.json
        parser.add_argument('--file', default='compounds.json',
                            help='File containing compounds and state (store/register)')

    def run(self):
        """Run compound command"""
        which_action = self._args.action
        self.compounds = self.load_file()

        if which_action == 'store':
            self.store_comp()
            self.write_file()
        elif which_action == 'register':
            self.register_comp()
            self.write_file()
        else:
            self.search_comp()

    def load_file(self):
        """Load json file"""
        try:
            return json.load(open(self._args.file, 'r+'))
        except:
            return {}

    def write_file(self):
        with open(self._args.file, 'w+') as f:
            json.dump(self.compounds, f, indent=4)

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

        # Compound does not exist, so store it
        if registered_state is None:
            self.compounds[self._args.id] = {'state': 'registered', 'plate.well': []}
        # Give error if compound already registered
        elif registered_state:
            logging.error(f'Compound {self._args.id} is already registered')
        else:
            self.compounds[self._args.id] = {'state': 'registered'}

    def search_comp(self):
        """Search for a compound - gives id, state (stored, registered),
        and all plates.wells associated with it"""
        if self.is_registered() == None:
            print(f'Compound {self._args.id} does not exist')
        else:
            results = self.compounds[self._args.id]
            print(f'id: {self._args.id}')
            print(f'state: {results["state"]}')
            if results["plate.well"]:
                print(f'plates: {results["plate.well"]}')

    def is_registered(self):
        """Check state of compound - is it registered already?"""
        # Already stored or registered
        if self._args.id in self.compounds:
            return self.compounds[self._args.id]['state'] == 'registered'
        # Does not exist yet
        return None

# class Compound(object):
#     """Represents a compound a biologist would store/register"""
#     def __init__(self, id, state):
#         self._id = id
#         self.state = state
#
#     @property
#     def id(self):
#         """Compound ID"""
#         return self._id
#