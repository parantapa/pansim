"""PanSim Command Line Interface."""

import click

@click.command()
def cli():
    """PanSim: The Pandemic Simulator."""
    click.echo("Hello, World")

if __name__ == "__main__":
    click_completion.init()
    cli(prog_name="pansim")
