# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Module Name: main.py (ktr-display)
Description: A cli tool to display maps from Killing Time:Resurrected EX
Author: InZane84
Date: 4/16/2026
License: MIT
Copyright (c) 2026 InZane84
"""

import re, zipfile
from pathlib import Path
from io import BytesIO

import rich_click as click
from omg.wad import WAD
from omg.udmf import UMapEditor
from PIL import Image, ImageDraw

KTR_EX_CFG = "KillingTimeEX_UDMF.cfg"


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

def load_wadfile(wadfile) -> UMapEditor: # type: ignore
    try:
        wad = WAD(wadfile)

        #TODO allow choosing different maps within the wadfile
        wad = UMapEditor(wad.udmfmaps['MAP01']) # type: ignore
        #=====================================================
        print(f"ktr wadfile loaded: {wadfile}")
        return wad
    except Exception as e:
        print(f"Error loading WAD: {e}")

def load_pk3(pk3) -> dict: # type: ignore
    try:
        sprite_map = {}
        with zipfile.ZipFile(pk3, 'r') as archive:
            pk3_root = archive.namelist()
            for file_path in pk3_root:
                if file_path.startswith('sprites/') and file_path.lower().endswith('.png'):
                    sprite_name = Path(file_path).stem.upper()
                    sprite_map[sprite_name] = file_path
                    if "A1" in sprite_name or "A0" in sprite_name:
                        base_name = sprite_name[:4]
                        sprite_map[base_name] = file_path
        print(f"load_pk3: ktr assets loaded @ {pk3}")
        return sprite_map
    except Exception as e:
        print(f"load_pk3: error loading ktr assets @ {e}")

def load_monsters(KTR_EX_CFG) -> dict: # type: ignore
    """ load the monsters from the cfg file """
    
    try:
        content = Path(KTR_EX_CFG).read_text()
        monster_section_match = re.search(r'monsters\s*\{(.+)', content, re.DOTALL)
        if not monster_section_match:
            return "NO monsters detected!" # type: ignore
        monster_block = monster_section_match.group(1)
        id_block_pattern = re.compile(r'(\d+)\s*\{([^}]+)\}', re.DOTALL)
        sprite_pattern = re.compile(r'sprite\s*=\s*"([^"]+)"', re.IGNORECASE)
        monster_map = {}
        for match in id_block_pattern.finditer(monster_block):
            thing_id = int(match.group(1))
            body = match.group(2)
            sprite_match = sprite_pattern.search(body)
            if sprite_match:
                full_sprite = sprite_match.group(1).upper()
                base_sprite = full_sprite[:4]
                monster_map[thing_id] = base_sprite
        print(f"load_monsters: ktr monsters loaded!")
        return monster_map
    except Exception as e:
        print("error loading monsters")

def get_map_bounds(udmf_map):
    v0 = udmf_map.vertexes[0]
    min_x = max_x = v0.x
    min_y = max_y = v0.y

    for v in udmf_map.vertexes:
        if v.x < min_x: min_x = v.x
        if v.x > max_x: max_x = v.x
        if v.y < min_y: min_y = v.y
        if v.y > max_y: max_y = v.y
    
    width = max_x - min_x
    height = max_y - min_y

    return min_x, min_y, max_x, max_y, width, height

@click.command(
        epilog="""
        [bold cyan]Example Usage: [/bold cyan]
        ktr-display MAP01.wad /path/to/ktr.kex(pk3)

        [dim]Note: Both files must be provided for the program to start[/dim]
        """
)
@click.argument('wadfile', type=click.Path(exists=True))
@click.argument('pk3', type=click.Path(exists=True))
@click.option('--output', '-o', default='MAP_preview.png', help='Output filename and path.', metavar='<PATH>')
@click.option('--scale', '-s', type=float, default=0.1, help='Scale factor.')
@click.option('--things/--no-things', '-t/-nt', default=False, help='Toggle drawing monsters.')
def main(wadfile, pk3, output, scale, things):
    """
    [bold red]KTR Display[/bold red] - Displays levels from Killing Time:Resurrected EX
    """

    wad = load_wadfile(wadfile)
    assets = load_pk3(pk3)
    monsters = load_monsters(KTR_EX_CFG)
    assets_path = pk3
    
    im_out = output
    SCALE = scale

    if wad and assets and monsters:       
        # 'map space(world)' uses a Cartesian plane (Y goes up), but
        # Pillow uses an image plane (Y goes down).
        # So we must offset by minimums and flip the Y-axis
        min_x, min_y, max_x, max_y, width, height = get_map_bounds(wad)
        # Create the canvas
        img_w = int(width * SCALE) + 100
        img_h = int(height * SCALE) + 100
        canvas = Image.new("RGBA", (img_w, img_h),(0, 0, 0))

        def to_pixels(x, y):
            """ convert a vertex(x, y) to a pixel(px, py) """
            px = int((x - min_x) * SCALE) + 50
            py = int((max_y - y) * SCALE) + 50
            return px, py
        
        draw = ImageDraw.Draw(canvas)
        for line in wad.linedefs:
            v1 = wad.vertexes[line.v1]
            v2 = wad.vertexes[line.v2]
            start_pos = to_pixels(v1.x, v1.y)
            end_pos = to_pixels(v2.x, v2.y)
            line_color = (200, 200, 200)
            if line.twosided:
                line_color = (100, 100, 100)
            draw.line([start_pos, end_pos], fill=line_color, width=1)
        if things:
            sprite_width = 150
            sprite_heigth = 150
            with zipfile.ZipFile(pk3, 'r') as archive:
                for thing in wad.things:
                    if thing.type in monsters:
                        base_sprite = monsters[thing.type]
                        image_path = assets[base_sprite]
                        with archive.open(image_path) as f:
                            sprite_image = Image.open(BytesIO(f.read())).convert("RGBA")
                        new_size = (int(sprite_image.width * SCALE), int(sprite_image.height * SCALE))
                        sprite_image = sprite_image.resize(new_size, Image.Resampling.NEAREST)
                        cx, cy = to_pixels(thing.x, thing.y)
                        overlay_pos = (cx - (sprite_image.width // 2),
                                       cy - (sprite_image.height // 2))
                        canvas.paste(sprite_image, overlay_pos, sprite_image)
        canvas.save(im_out)
        click.echo(f"wrote image to {im_out}")

if __name__ == "__main__":
    main()
