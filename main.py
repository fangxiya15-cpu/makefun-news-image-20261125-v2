#!/usr/bin/env python3
"""Entry program for make.fun's news-image-20261125 bounty.

Writes the day's news image to /output/entry.png. The image ships in
this repository as entry.png (composed by src/compose.py from
src/day-20261125-v2.json, the evening edition); this program copies it
byte for byte, so both grading runs produce identical bytes and no
network is needed.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST = "/output/entry.png"


def main():
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    shutil.copyfile(SRC, DST)


if __name__ == "__main__":
    main()
