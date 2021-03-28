import string

from kaleido.command import Command

alphabet = list(string.ascii_uppercase)
#############################################################################################
#   USE CASE                                                                                #
#   As a Biologist,                                                                         #
#   I would like to create a plate                                                          #
#   so that I can keep track of experiments                                                 #
#############################################################################################

class PlateCommand(Command):
    """Create a plate containing wells for experiments"""

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('id', type=str, help='Plate ID')
        parser.add_argument('--create', metavar=('width', 'height'),
                            nargs=2, type=int, help='Create a plate with dimensions (width, height)')
        parser.add_argument('--search', action='store_true', help='Search for a plate')

    def run(self):
        if self._args.create:
            plate = Plate(self._args.id, self._args.create[0], self._args.create[1])
            plate.display()

class Plate:
    def __init__(self, id, width, height):
        self.id = id
        self.width = width
        self.height = height
        self.rows = alphabet[:height]
        self.cols = list(range(1, width + 1))

    def display(self):
        # Print the well number
        print('\t' + '\t'.join(map(str, self.cols)))
        # Print well letter and co
        for i in range(self.height):
            print('{}'.format(self.rows[i]))