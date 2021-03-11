#!/usr/bin/env python

import sys
from fftools import get_frames, get_stream_info
import argparse

#
# main
#
ap = argparse.ArgumentParser(
        description="show stat of GOP. it reads 10000 frames by default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", help="video file.")
ap.add_argument("-N", action="store_false", dest="show_stat",
                help="disable to show stat.")
ap.add_argument("-p", action="store_true", dest="show_pattern",
                help="show GOP patterns.")
ap.add_argument("--no-newline", action="store_false", dest="add_newline",
                help="disable to add a new line before a key frame.")
ap.add_argument("-F", "--frames", action="store", dest="max_frames",
                type=int, default=10000,
                help="specify max frames to be read.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

ffinfo = get_stream_info(opt.input_file, codec_type="video",
                         verbose=opt.verbose)[0]

frames = get_frames(opt.input_file, max_frames=opt.max_frames,
                    entries=["key_frame", "pict_type", "pkt_pts_time"],
                    verbose=opt.verbose)

def tosymbol(x):
    if x["key_frame"] == "1":
        if x["pict_type"] == "I":
            return "I"
        else:
            # NOTE: key frame and not pict_type, it should not be in case.
            return "X"
    else:
        return x["pict_type"]

if not opt.show_pattern:
    print("nb   Size Pattern")
    print("==== ==== =======")
    patt_stat = {}
    patt = [ tosymbol(frames[0]) ]
    for x in frames[1:]:
        if x["key_frame"] == "1":
            p = "{}".format("".join(patt))
            patt_stat.setdefault(p, 0)
            patt_stat[p] += 1
            patt = []
        patt.append(tosymbol(x))
    #
    for k,v in patt_stat.items():
        print("{:4} {:4} {}".format(v, len(k), k))
else:
    print("Size Pattern")
    print("==== =======")
    if opt.add_newline:
        nl = "\n"
    else:
        nl = ""
    #
    patt = [ tosymbol(frames[0]) ]
    for x in frames[1:]:
        if x["key_frame"] == "1":
            sys.stdout.write("{:4} {}{}".format(len(patt),"".join(patt),nl))
            patt = []
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
