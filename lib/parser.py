import argparse

def get_parser():
    parser = argparse.ArgumentParser(
        description="Makes a sprite or bgrect object compatible with N64 S2DEX microcodes.\n"+
        "N.I. stands for \"Not Implemented\""
    )

    parser.add_argument(
        "-i",
        dest="input_file",
        metavar="FILE",
        help="Input file (MUST be a .png). If a folder is specified, defaults to animation mode.",
        required=True,
    )

    parser.add_argument(
        "-o",
        dest="output_file",
        help="Output file (Stores texture data, and the S2DEX structure)",
        required=True,
    )

    parser.add_argument(
        "-f",
        dest="header_file",
        metavar="FILE",
        help="Optional header file with appropriate externs",
    )

    parser.add_argument(
    	"-c",
        "--create-dl",
        dest="create_dl",
        action="store_true",
        help="Creates a simple displaylist to render the sprite or bg",
    )

    parser.add_argument(
    	"-b",
        "--bgrect",
        dest="bgrect",
        action="store_true",
        help="Makes a BG rect instead of a sprite. Only compatible with single files.",
    )

    parser.add_argument(
    	"-n",
        "--name",
        dest="sprite_name",
        help="Sprite/BGRect object name (Defaults to 'sprite')",
        default="sprite",
    )

    parser.add_argument(
    	"-d",
        "--dlheadname",
        dest="dl_head",
        help="Name of gdl head (default gDisplayListHead for SM64 decomp)",
        default="gDisplayListHead",
    )

    parser.add_argument(
    	"-t",
        "--makeinitdl",
        dest="init_dl",
        action="store_true",
        help="Creates an S2D init DL which sets up the RDP correctly",
    )

    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["RGBA16", "RGBA32", "IA8", "CI4", "I4"],
        help="Image Format (default RGBA16).",
        default="RGBA16",
    )

    parser.add_argument(
        "-p",
        "--palette-split",
        dest="pal_split",
        action="store_true",
        help="(CI4 Only) Assigns one palette per CI4 frame in an animation.",
    )

    parser.add_argument(
        "-k",
        "--makefont",
        dest="isfont",
        action="store_true",
        help="(S2D Text Engine) Optimizes the output file for use with Text Engine.",
    )

    parser.add_argument(
    	"-a",
        "--autoresize",
        dest="autoresize",
        action="store_true",
        help="(N.I.) If a sprite/object isn't sized correctly for LoadBlock, resize it automatically",
    )


    return parser
