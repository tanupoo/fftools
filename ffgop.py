#!/usr/bin/env python

import sys
from subprocess import Popen, PIPE
import shlex
import argparse

"""
packet|codec_type=video|stream_index=0|pts=0|pts_time=0.000000|dts=0|dts_time=0.000000|duration=N/A|duration_time=N/A|convergence_duration=N/A|convergence_duration_time=N/A|size=790|pos=97831|flags=__
packet|codec_type=video|stream_index=0|pts=166834|pts_time=0.166834|dts=1|dts_time=0.000001|duration=N/A|duration_time=N/A|convergence_duration=N/A|convergence_duration_time=N/A|size=24|pos=98621|flags=__
packet|codec_type=video|stream_index=0|pts=100100|pts_time=0.100100|dts=33367|dts_time=0.033367|duration=N/A|duration_time=N/A|convergence_duration=N/A|convergence_duration_time=N/A|size=21|pos=98645|flags=__
"""

"""
frame|media_type=video|stream_index=0|key_frame=1|pkt_pts=0|pkt_pts_time=0.000000|pkt_dts=133467|pkt_dts_time=0.133467|best_effort_timestamp=0|best_effort_timestamp_time=0.000000|pkt_duration=N/A|pkt_duration_time=N/A|pkt_pos=97831|pkt_size=790|width=720|height=480|pix_fmt=yuv420p|sample_aspect_ratio=853:720|pict_type=I|coded_picture_number=0|display_picture_number=0|interlaced_frame=0|top_field_first=0|repeat_pict=0|color_range=unknown|color_space=unknown|color_primaries=unknown|color_transfer=unknown|chroma_location=left

frame|media_type=video|stream_index=0|key_frame=0|pkt_pts=66733|pkt_pts_time=0.066733|pkt_dts=166833|pkt_dts_time=0.166833|best_effort_timestamp=66733|best_effort_timestamp_time=0.066733|pkt_duration=N/A|pkt_duration_time=N/A|pkt_pos=98666|pkt_size=21|width=720|height=480|pix_fmt=yuv420p|sample_aspect_ratio=853:720|pict_type=B|coded_picture_number=3|display_picture_number=0|interlaced_frame=0|top_field_first=0|repeat_pict=0|color_range=unknown|color_space=unknown|color_primaries=unknown|color_transfer=unknown|chroma_location=left
frame|media_type=video|stream_index=0|key_frame=0|pkt_pts=100100|pkt_pts_time=0.100100|pkt_dts=200200|pkt_dts_time=0.200200|best_effort_timestamp=100100|best_effort_timestamp_time=0.100100|pkt_duration=N/A|pkt_duration_time=N/A|pkt_pos=98645|pkt_size=21|width=720|height=480|pix_fmt=yuv420p|sample_aspect_ratio=853:720|pict_type=B|coded_picture_number=2|display_picture_number=0|interlaced_frame=0|top_field_first=0|repeat_pict=0|color_range=unknown|color_space=unknown|color_primaries=unknown|color_transfer=unknown|chroma_location=left
frame|media_type=video|stream_index=0|key_frame=0|pkt_pts=133467|pkt_pts_time=0.133467|pkt_dts=233567|pkt_dts_time=0.233567|best_effort_timestamp=133467|best_effort_timestamp_time=0.133467|pkt_duration=N/A|pkt_duration_time=N/A|pkt_pos=98687|pkt_size=21|width=720|height=480|pix_fmt=yuv420p|sample_aspect_ratio=853:720|pict_type=B|coded_picture_number=4|display_picture_number=0|interlaced_frame=0|top_field_first=0|repeat_pict=0|color_range=unknown|color_space=unknown|color_primaries=unknown|color_transfer=unknown|chroma_location=left
frame|media_type=video|stream_index=0|key_frame=0|pkt_pts=166834|pkt_pts_time=0.166834|pkt_dts=266933|pkt_dts_time=0.266933|best_effort_timestamp=166834|best_effort_timestamp_time=0.166834|pkt_duration=N/A|pkt_duration_time=N/A|pkt_pos=98621|pkt_size=24|width=720|height=480|pix_fmt=yuv420p|sample_aspect_ratio=853:720|pict_type=P|coded_picture_number=1|display_picture_number=0|interlaced_frame=0|top_field_first=0|repeat_pict=0|color_range=unknown|color_space=unknown|color_primaries=unknown|color_transfer=unknown|chroma_location=left
"""

def get_frames(opt):
    base_cmd = "ffprobe -v error -of compact -select_streams v -show_frames -i"
    cmd = f"{base_cmd} {opt.input_file}"
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
    p = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE,
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
        if opt.max_lines and nb_lines > opt.max_lines:
            break

    if p.poll():
        print(f"ERROR: {p.stderr.read().decode()}")

    return frames

#
# main
#
ap = argparse.ArgumentParser(
        description="this is example.",
        epilog="this is the tail story.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", help="1st item.")
ap.add_argument("-p", action="store_true", dest="show_pattern",
                help="pattern.")
ap.add_argument("--no-newline", action="store_false", dest="add_newline",
                help="disable to add a new line before a key frame.")
ap.add_argument("--lines", action="store", dest="max_lines",
                type=int, default=0,
                help="specify max lines to be read.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

frames = get_frames(opt)

if opt.show_pattern:
    nl = ""
    if opt.add_newline:
        nl = "\n"
    for x in frames:
        if x["key_frame"] == "1":
            sys.stdout.write(nl)
            if x["pict_type"] == "I":
                sys.stdout.write("I")
            else:
                sys.stdout.write("i")
        else:
            sys.stdout.write(x["pict_type"])
    print()
    exit(0)

# default
gos = []
for x in frames:
    if x.get("key_frame", "0") == "1":
        if x["pict_type"] != "I":
            print("WARNING: key frame, but type {}.".format(x["pict_type"]))
        gos.append(float(x["pkt_pts_time"]))

if len(gos) > 1:
    gos_time = [ b-a for a,b in zip(gos[:-1], gos[1:]) ]
    print("avr = ", round(sum(gos_time)/len(gos_time),6))
    print("max = ", round(max(gos_time),6))
    print("min = ", round(min(gos_time),6))
else:
    print("NOTE: no enough key frame found. len={}", len(gos))
