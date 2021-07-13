"""PanSim Command Line Interface."""

import click
import click_completion

from . import cli

from .simplesim import simplesim
from .partition import partition
from .distsim import distsim


@click.group()
def cli():
    """PanSim: The Pandemic Simulator."""


cli.add_command(partition)
cli.add_command(simplesim)
cli.add_command(distsim)

if __name__ == "__main__":
    click_completion.init()
    cli(prog_name="pansim")
