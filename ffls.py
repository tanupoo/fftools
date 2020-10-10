#!/usr/bin/env python

import sys
import os
from stat import S_ISDIR
from fftools import get_stream_info
import glob
import argparse
import shlex
from datetime import time

MIN_BITRATE = 4000000
MAX_BITRATE = 9999999999

def print_info(path, **kwargs):
    def get_duration(duration, short_format=True):
        d = round(float(duration),6)
        m, s = divmod(int(d),60)
        t = time(minute=m, second=s, microsecond=int((d-int(d))*1000000))
        # '09:08.648099'
        if short_format:
            return t.isoformat()[3:12]
        else:
            return t.isoformat()[3:]
    #
    prefixes = kwargs.get("prefixes", ".mp4")
    codec_type = kwargs.get("codec_type", "video")
    min_bitrate = kwargs.get("min_bitrate", MIN_BITRATE)
    max_bitrate = kwargs.get("max_bitrate", MAX_BITRATE)
    show_only_name = kwargs.get("show_only_name", False)
    check_bitrate = kwargs.get("check_bitrate", False)
    verbose = kwargs.get("verbose", False)
    filename, ext = os.path.splitext(path)
    #
    if ext in prefixes:
        try:
            info_v = get_stream_info(path, codec_type=codec_type)[0]
        except Exception as e:
            #print("ERROR:", e)
            # just ignore
            return
        # check if ignore it.
        bitrate = int(info_v["bit_rate"])
        if check_bitrate and (bitrate > max_bitrate or bitrate < min_bitrate):
            # ignore it
            return
        if show_only_name:
            print(f"{path}", flush=True)
            return
        # set name of the file.
        if verbose:
            name = filename
        else:
            name = filename[:40]
        # "bitrate", "width", "height", "duration", 
        if True: # full
            cols = [ "profile", "level", "
        print(fmt_body.format(
                int(bitrate/1000), # kbps
                info_v["width"],
                info_v["height"],
                get_duration(info_v["duration"], short_format=True),
                name))

def walk_path(path, recursive=False, func=None, fargs=None):
    #print(f"ent: {path}")

    # here, a path string is passed to os.stat()
    mode = os.stat(path).st_mode
    if not S_ISDIR(mode):   # XXX enough to check if it's a file ?
        if func is not None:
            func(path, **fargs)
    else:
        with os.scandir(path) as fd:
            for entry in fd:
                if entry.name.startswith(".."):
                    continue
                elif entry.is_dir():
                    if recursive:
                        walk_path(entry.path, recursive, func, fargs)
                else:
                    walk_path(entry.path, recursive, func, fargs)

# main
prefixes = [".mp4"]
ap = argparse.ArgumentParser(
        description="this is example.",
        epilog="this is the tail story.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="*", help="a file name")
ap.add_argument("-c", action="store_true", dest="check_bitrate",
                help="take into account of the range of bitrates.")
ap.add_argument("--max-bitrate", action="store", dest="max_bitrate",
                type=int, default=MAX_BITRATE,
                help="specify maximum bitrate of a file to show.")
ap.add_argument("--min-bitrate", action="store", dest="min_bitrate",
                type=int, default=MIN_BITRATE,
                help="specify minimum bitrate of a file to show.")
ap.add_argument("--x-check-bitrate", action="store_true", dest="x_bitrate",
                help="for test, certain bitrate range of 4100 and 3900.")
ap.add_argument("--prefixes", action="store", dest="_prefixes",
                default="mp4",
                help="specify prefixes to show, comma separated. "
                "e.g. mp4,flv")
ap.add_argument("-p", action="store_true", dest="show_only_name",
                help="enable to show the list of files.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="enable verbose mode.")
opt = ap.parse_args()

if opt._prefixes is None:
    opt._prefixes = ".mp4"
if opt.x_bitrate:
    opt.max_bitrate = 4100000
    opt.min_bitrate = 3900000
opt.prefixes = [ f".{x}" for x in opt._prefixes.split(",") ]

# header
headers = [ "kbps", "W   ", "H   ", "Duration ", "Filename" ]
fmt_header = " ".join([ f"{{:{len(i)}}}" for i in headers ])
fmt_body = " ".join([ f"{{:{len(i)}}}" for i in headers[:-1] ] + ["{}"])
print(fmt_header.format(*headers))
print(" ".join([ "-"*len(i) for i in headers ]))
# body
if len(opt.input_file) == 0:
    opt.input_file = ["."]
for f in opt.input_file:
    walk_path(f, recursive=False,
              func=print_info, fargs=dict(opt._get_kwargs()))

