#!/usr/bin/env python

import os
from stat import S_ISDIR
from fftools import get_stream_info, ffPrintInfo
import argparse

MIN_BITRATE = 4000000
MAX_BITRATE = 9999999999

def print_info(path):
    filename, ext = os.path.splitext(path)
    if opt.prefixes is None or ext in opt.prefixes:
        try:
            ffinfo = get_stream_info(path, codec_type="video",
                                     verbose=opt.verbose)[0]
        except Exception as e:
            if opt.verbose:
                print("ERROR:", e)
            return
        # check if ignore it.
        if opt.check_bitrate:
            try:
                bitrate = int(ffinfo["bit_rate"])
            except KeyError:
                pass
            except ValueError:
                pass
            else:
                if (bitrate > opt.max_bitrate or bitrate < opt.min_bitrate):
                    # ignore it
                    return
        #
        if opt.show_only_name:
            print(f"{path}", flush=True)
            return
        #
        ffprint.print_info(ffinfo)

def walk_path(path, recursive=False):
    if opt.verbose:
        print(f"PATH: {path}")
    try:
        mode = os.stat(path).st_mode
    except Exception as e:
        print(path, e)
        return
    #
    if not S_ISDIR(mode):
        print_info(path)
    else:
        with os.scandir(path) as fd:
            for entry in fd:
                if entry.name.startswith(".."):
                    continue
                elif entry.is_dir():
                    if recursive:
                        walk_path(entry.path, recursive)
                else:
                    walk_path(entry.path, recursive)

# main
ap = argparse.ArgumentParser(
        description="list video files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="*", help="a file name")
ap.add_argument("-l", action="append_const", dest="_print_mode",
                default=[], const=1,
                help="enable to show long info.  -l -l can be show more info.")
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
ap.add_argument("-p", action="store", dest="prefixes",
                default="mp4,mkv,avi,flv,vob,wmv,mov,mpg,m4v,webm",
                help="specify prefixes to show, comma separated. "
                "e.g. mp4,flv")
ap.add_argument("-n", action="store_true", dest="show_only_name",
                help="enable to show the list of files.")
ap.add_argument("-r", action="store_true", dest="recursively",
                help="enable to recursively search the directory.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="enable verbose mode.")
opt = ap.parse_args()

opt.print_mode = len(opt._print_mode)
opt.prefixes = [ f".{x}" for x in opt.prefixes.split(",") ]
if opt.x_bitrate:
    opt.max_bitrate = 4100000
    opt.min_bitrate = 3900000

# header
ffprint = ffPrintInfo(print_mode=opt.print_mode, verbose=opt.verbose)
ffprint.print_header()

# body
if len(opt.input_file) == 0:
    opt.input_file = ["."]
for f in opt.input_file:
    walk_path(f, recursive=opt.recursively)

