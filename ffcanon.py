#!/usr/bin/env python

import sys
import unicodedata
from subprocess import Popen, PIPE, DEVNULL
import shlex
import os
import json
import math
from fftools import get_stream_info, ffPrintInfo, progress_bar
import re
import glob

def do_main(input_file, quoted=False):
    ffinfo = get_stream_info(input_file, codec_type="video",
                              verbose=opt.verbose)[0]
    #
    print(f"## video stream profile: {input_file}")
    ffprint = ffPrintInfo(print_mode=1, verbose=opt.verbose)
    ffprint.print_header()
    ffprint.print_info(input_file, ffinfo)
    if opt.show_profile:
        return
    #
    if ffinfo["width"] < 1920 and not opt.force:
        print("no need to resize.")
        return
    #
    nb_frames = int(ffinfo.get("nb_frames","0"))
    #
    if opt.output_file is None:
        bname, prefix = os.path.splitext(input_file)
        bname = unicodedata.normalize("NFC", bname)
        output_file  = f"{bname}-dst.mp4"
    else:
        output_file  = opt.output_file
    #
    opts = []
    #opts.append("-progress")
    if opt.overwrite:
        opts.append("-y")
    if opt.no_audio:
        opts.append("-an")
    #
    opts.append("-profile:v high")
    if opt.profile_level is not None:
        opts.append(f"-level:v {opt.profile_level}")
    else:
        opts.append("-level:v {}".format(ffinfo["level"]))
    #
    vf_opt = []
    if opt.scale is not None:
        vf_opt.append(f"scale={opt.scale}:-1")
    else:
        vf_opt.append("scale=1280:-1")
    if opt.rotate is not None:
        if opt.rotate.lower() in ["r", "right"]:
            vf_opt.append("transpose=1")
        elif opt.rotate.lower() in ["l", "left"]:
            vf_opt.append("transpose=2")
        else:
            # just ignore it.
            pass
    opts.append("-vf " + ",".join(vf_opt))
    opts = " ".join(opts)

    cmd = (f"ffmpeg -i {shlex.quote(input_file)} "
        f"{opts} "
        f"{shlex.quote(output_file)}")
    print("===>", cmd)
    p = Popen(shlex.split(cmd), stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
            universal_newlines=True
            )

    while True:
        buf = p.stderr.readline()
        if not buf:
            break
        # frame=  671 fps= 19 q=-1.0 Lsize=   63844kB time=00:06:01.49 bitrate=1446.8kbits/s dup=380 drop=387 speed=0.324x    
        r = re.search("frame=\s*(\d+) .*", buf)
        if r:
            progress_bar(int(r.group(1)), nb_frames)

    p.wait()

#
#
#
import argparse
ap = argparse.ArgumentParser(
        description="convert video file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="+", help="a movie file.")
ap.add_argument("--output", action="store", dest="output_file",
                help="specify the filename converted.")
ap.add_argument("--level", action="store", dest="profile_level",
                help="specify the profile level.")
ap.add_argument("--scale", action="store", dest="scale",
                type=int, default=1280,
                help="specify the scale.")
ap.add_argument("--rotate", action="store", dest="rotate",
                default=None, choices=["right", "r", "left", "l"],
                help="specify the direction of 90 rotation.")
ap.add_argument("--time-start", action="store", dest="start_time",
                help="pass the value to ffmpeg the -ss option.")
ap.add_argument("--time-end", action="store", dest="end_time",
                help="pass the value to ffmpeg the -to option.")
ap.add_argument("--time-duration", action="store", dest="end_time",
                help="pass the value to ffmpeg the -t option.")
ap.add_argument("-an", action="store_true", dest="no_audio",
                help="remove audio..")
ap.add_argument("-f", action="store_true", dest="force",
                help="force to convert the file.")
ap.add_argument("-y", action="store_true", dest="overwrite",
                help="overwrite the output file.")
ap.add_argument("-p", action="store_true", dest="show_profile",
                help="show only profile.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

##
if opt.input_file == ["-"]:
    for f in sys.stdin:
        do_main(f.strip())
else:
    for f in opt.input_file:
        do_main(f.strip())

