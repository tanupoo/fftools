#!/usr/bin/env python

import sys
from subprocess import Popen, PIPE, DEVNULL
import shlex
import argparse

def get_frames(opt):
    cmd = ("ffprobe -v error -of compact -select_streams v -show_frames "
           f"-i {shlex.quote(opt.input_file)}")
    if opt.verbose:
        print("CMD==>", cmd)
    #
    frames = []
    """
    key_list = [
        "media_type", "stream_index", "key_frame",
        "pkt_pts", "pkt_pts_time", "pkt_dts", "pkt_dts_time",
        "best_effort_timestamp", "best_effort_timestamp_time",
        "pkt_duration", "pkt_duration_time", "pkt_pos",
        "pkt_size", "width", "height", "pix_fmt",
        "sample_aspect_ratio", "pict_type", "coded_picture_number",
        "display_picture_number", "interlaced_frame", "top_field_first",
        "repeat_pict", "color_range", "color_space", "color_primaries",
        "color_transfer", "chroma_location",
        ]
    """
    p = Popen(shlex.split(cmd), stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    nb_lines = 1
    while p.poll() is None:
        cols = p.stdout.readline().strip().split("|")
        if opt.verbose:
            print("COL:", cols)
        if cols[0] != "frame":
            # it's not a frame info, just to be ignored.
            continue
        if len(cols) != 29:
            print("WARNING: len != 29:", cols, file=sys.stderr)
            continue
        frames.append(dict(x.split("=") for x in cols[1:]))
        # another condition to break
        nb_lines += 1
        if opt.max_frames and nb_lines > opt.max_frames:
            break

    if p.poll():
        print(f"ERROR: {p.stderr.read()}")

    return frames

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
                type=int, default=100000,
                help="specify max frames to be read.")
ap.add_argument("-n", action="store_false", dest="show_stat",
                help="disable to show stat.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

frames = get_frames(opt)

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
    if opt.add_newline:
        nl = "\n"
    else:
        nl = ""
    sys.stdout.write(tosymbol(frames[0]))
    for x in frames[1:]:
        if x["key_frame"] == "1":
            sys.stdout.write(nl)
        sys.stdout.write(tosymbol(x))
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
