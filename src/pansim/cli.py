"""PanSim Command Line Interface."""

import click
import click_completion

from .simplesim import simplesim
from .distsim import distsim


@click.group()
def cli():
    """PanSim: The Pandemic Simulator."""


cli.add_command(simplesim)
cli.add_command(distsim)
click_completion.init()
