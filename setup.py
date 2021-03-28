from setuptools import setup

setup(
    name='kaleido',
    version='1.0',
    description='Kaleido Interview - Determining Well Compound',
    maintainer='Elysha Sameth',
    maintainer_email='esameth1@gmail.com',
    url='https://github.com/esameth/kaleido',

    classifiers=['Programming Language :: Python :: 3.7'],

    entry_points='''
        [console_scripts]
        kaleido = kaleido.command:main

        [kaleido.commands]
        compound = kaleido.commands.compound:CompoundCommand
        plate = kaleido.commands.plate:PlateCommand
    ''',

    test_suite='kaleido.tests',
)