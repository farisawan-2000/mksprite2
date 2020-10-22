# mksprite2
### Create sprite and background objects for use with S2DEX microcode projects on Nintendo 64!

## Usage
`python3 mksprite.py -h` for full help

`-i`: **Input file/Folder** - Specify an image for a single sprite (Must be a .png file), or a folder for animated sprites. All frames of animated sprites must use the naming scheme `X.png`, where X is the frame number

`-o`: **Output file** - Where the output textures, uObjTxtr, and uObjSprite/uObjBgRect will end up

`-n`: **Sprite name** - Used as a base for what a sprite should be named. Defaults to `sprite`
