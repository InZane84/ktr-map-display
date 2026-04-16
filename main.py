# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Module Name: main.py (ktr-display)
Description: A cli tool to display maps from Killing Time:Resurrected
Author: InZane84
Date: 4/16/2026
License: MIT
Copyright (c) 2026 InZane84
"""

import re, zipfile, io
from pathlib import Path
import rich_click as click
from omg.wad import WAD
from omg.udmf import UMapEditor



click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "ktr-display": [
        {"name": "Input Files", "options":["wadfile", "pk3"]},
        {"name": "Help,", "options":["--help"]},
    ]
}

click.rich_click.COMMAND_GROUPS = {
    "ktr-display": [{"name": "Commands", "commands": ["main"]}]
}

def load_wadfile(wadfile):
    try:
        wad = WAD(wadfile)

        #TODO allow choosing different maps within the wadfile
        wad = UMapEditor(wad.udmfmaps['MAP01'])
        #=====================================================
        print(f"ktr wadfile loaded: {wadfile}")
        return wad
    except Exception as e:
        print(f"Error loading WAD: {e}")

def load_pk3(pk3):
    try:
        pk3 = "foo"
        print(f"ktr assets loaded: {pk3}")
        return pk3
    except Exception as e:
        print(f"Error loading ktr assets: {e}")


@click.command(
        epilog="""
        [bold cyan]Example Usage: [/bold cyan]
        ktr-display MAP01.wad /path/to/ktr.kex(pk3)

        [dim]Note: Both files must be provided for the program to start[/dim]
        """
)
@click.argument('wadfile', type=click.Path(exists=True))
@click.argument('pk3', type=click.Path(exists=True))
def main(wadfile, pk3):
    """
    [bold red]KTR Display[/bold red] - Displays images for Killing Time:Resurrected
    """

    click.echo(f"Loading mah stuff...")
    wad = load_wadfile(wadfile)
    assets = load_pk3(pk3)
    
    if wad and assets:
        print("Good to go!")
        print(wad.things[3].type)


#    main.epilog = "Example: ktr-display MAP01.wad ktr.pk3"

if __name__ == "__main__":
    main()
