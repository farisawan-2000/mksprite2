# mksprite2
### Create sprite and background objects for use with S2DEX microcode projects on Nintendo 64

## Usage
`./mksprite2.py -h` for full help

`-i FILE_NAME`: **Input file/Folder** - Specify an image for a single sprite (Must be a .png file), or a folder for animated sprites. All frames of animated sprites must use the naming scheme `X.png`, where X is the frame number

`-o FILE_NAME`: **Output file** - Where the output textures, uObjTxtr, and uObjSprite/uObjBgRect will end up

`-n SPR_NAME`: **Sprite name** - Used as a base for what a sprite should be named. Defaults to `sprite`

## Gotchas and Things To Watch Out For
- When using the tool with the 2.0L version of SM64 decomp, there are a ton of space limitations with unknown causes. You will likely have to split the resulting output file into a file with just textures and a file with just the sprite-related data.
- RGBA32 textures do not work (but feel free to try to get them to work and PR the changes)
- The GNU GPLv3 License

### Full Options List
```
usage: mksprite2.py [-h] -i FILE -o OUTPUT_FILE [-f FILE] [-c] [-b] [-n SPRITE_NAME] [-d DL_HEAD] [-t] [-a]

Makes a sprite or bgrect object compatible with N64 S2DEX microcodes. N.I. stands for "Not Implemented"

optional arguments:
  -h, --help            show this help message and exit
  -i FILE               Input file (MUST be a .png). If a folder is specified, defaults to animation mode.
  -o OUTPUT_FILE        Output file (Stores texture data, and the S2DEX structure)
  -f FILE               Optional header file which will contain appropriate externs
  -c, --create-dl       Creates a simple displaylist to render the sprite or bg
  -b, --bgrect          Makes a BG rect instead of a sprite. Only compatible with single files.
  -n SPRITE_NAME, --name SPRITE_NAME
                        Sprite/BGRect object name (Defaults to 'sprite')
  -d DL_HEAD, --dlheadname DL_HEAD
                        Name of gdl head for animated sprites (default gDisplayListHead for sm64 decomp)
  -t, --makeinitdl      Creates an S2D init DL which sets up the RDP correctly
  -a, --autoresize      (Not Implemented) If a sprite/object isn't sized correctly for LoadBlock, resize it automatically
  ```
