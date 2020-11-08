"""PanSim Command Line Interface."""


import click_completion

from . import cli

from .simplesim import simplesim
from .partition import partition
from .distsim import distsim

if __name__ == "__main__":
    click_completion.init()
    cli(prog_name="pansim")
