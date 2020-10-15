#!/usr/bin/env python

import sys
from fftools import get_frames
import argparse

#
# main
#
ap = argparse.ArgumentParser(
        description="show stat of GOP.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", help="video file.")
ap.add_argument("-p", action="store_true", dest="show_pattern",
                help="pattern.")
ap.add_argument("--no-newline", action="store_false", dest="add_newline",
                help="disable to add a new line before a key frame.")
ap.add_argument("--frames", action="store", dest="max_frames",
                type=int,
                help="specify max frames to be read.")
ap.add_argument("-n", action="store_false", dest="show_stat",
                help="disable to show stat.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

# set default frames to be read.
if opt.max_frames is None:
    if opt.show_pattern:
        opt.max_frames = 300
    else:
        opt.max_frames = 10000

frames = get_frames(opt.input_file, max_frames=opt.max_frames,
                    entries=["key_frame", "pict_type", "pkt_pts_time"],
                    verbose=opt.verbose)

if opt.show_pattern:
    def tosymbol(x):
        if x["key_frame"] == "1":
            if x["pict_type"] == "I":
                return "I"
            else:
                # NOTE: key frame and not pict_type, it should not be in case.
                return "X"
        else:
            return x["pict_type"]
    #
    print("Size Pattern")
    print("==== =======")
    if opt.add_newline:
        nl = "\n"
    else:
        nl = ""
    patt = [ tosymbol(frames[0]) ]
    for x in frames[1:]:
        if x["key_frame"] == "1":
            sys.stdout.write("{:4} {}{}".format(len(patt),"".join(patt),nl))
        patt.append(tosymbol(x))
    print()

if opt.show_stat:
    gop = []
    for x in frames:
        if x.get("key_frame", "0") == "1":
            if x["pict_type"] != "I":
                print("WARNING: key frame, but type {}.".format(x["pict_type"]))
            gop.append(float(x["pkt_pts_time"]))

    if len(gop) > 1:
        gop_time = [ b-a for a,b in zip(gop[:-1], gop[1:]) ]
        print("## GOP size in seconds.")
        print("nb of GOP:", len(gop))
        print("avr time :", round(sum(gop_time)/len(gop_time),6))
        print("max time :", round(max(gop_time),6))
        print("min time :", round(min(gop_time),6))
    else:
        print("NOTE: no enough key frame found. len={}", len(gop))
