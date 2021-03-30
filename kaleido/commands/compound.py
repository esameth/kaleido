import sys
import logging
import argparse

from kaleido.command import Command
from kaleido.compounds import Compound
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

    def run(self):
        """Run compound command"""
        self.compounds = load_file(self._args.comp_file)
        self.comp = self.load_comp()

        if self._args.store:
            self.store_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.register:
            self.register_comp()
            write_file(self._args.comp_file, self.compounds)
        elif self._args.search:
            self.search_comp()

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
            print(f'id: {self.comp._id}')
            print(f'state: {self.comp.state}')
            if self.comp.plate:
                print('plates: {}'.format("\t".join(self.comp.plate)))

    def load_comp(self):
        # Already stored or registered
        if exists(self._args.id, self.compounds):
            return Compound(self._args.id, props=self.compounds[self._args.id])