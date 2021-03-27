# Contains all information for a command

import argparse
import logging
import pkg_resources

class CommandError(Exception):
    """Raised if there is in an error running Command.run()."""

class Command(object):
    """
    Represents a command (storing/registering a compound, adding a plate,
    adding a compound to the plate, retrieving a well)

    Command is executed using .run() and can initialize argparse to
    get all user arguments.
    """
    def __init__(self, args):
        self._args = args

    @classmethod
    def init_parser(cls, parser):
        """Initialize argparse.ArgumentParser."""

    def run(self):
        """Execute command"""

    def argument_error(self, msg):
        """Raise error indicating error parsing an argument."""
        raise CommandError(msg)

    def fail(self, msg, exc=None):
        """Exit command as a result of a failure."""
        logger.error(msg)
        if exc is not None:
            logger.debug('Command failed due to an exception!', exc_info=exc)
        sys.exit(1)

def main(command_class=None, args=None):
    """Run the command line with the given command"""

    title = 'Kaleido Interview'
    if command_class is not None:
        title, _, _ = command_class.__doc__.partition('\n\n')

    parser = argparse.ArgumentParser(description=title)

    if command_class is not None:
        # Command is given, run that command
        command_class.init_parser(parser)
        parser.set_defaults(command=command_class)
    else:
        # Get all available commands
        commands = {}
        for entry in pkg_resources.iter_entry_points('kaleido.commands'):
            canonical = entry.name.lower()
            if canonical not in commands:
                command_class = entry.load()
                commands[canonical] = command_class

        # Create parsers for subcommands
        subparsers = parser.add_subparsers(title='Commands', metavar='command')
        for name, command_class in sorted(commands.items()):
            title, _, _ = command_class.__doc__.partition('\n\n')
            subparser = subparsers.add_parser(
                name, help=title,
                description=command_class.__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
            subparser.set_defaults(command=command_class)
            command_class.init_parser(subparser)

    parsed_args = parser.parse_args(args)

    # Instantiate command and run
    command = parsed_args.command(parsed_args)
    try:
        command.run()
    except CommandError as error:
        parser.error(error)