#!/usr/bin/env python

import sys
import unicodedata
from subprocess import Popen, PIPE, DEVNULL
import shlex
import os
from fftools import (get_stream_info, get_duration,
                     ffPrintInfo, progress_bar, parse_time)
import re
from datetime import timedelta

_DEFAULT_SCALE = 1280

def do_main(input_file, quoted=False):
    ffinfo = get_stream_info(input_file, codec_type="video",
                              verbose=opt.verbose)[0]
    #
    print(f"## video stream profile: {input_file}")
    ffprint = ffPrintInfo(print_mode=1, verbose=opt.verbose)
    ffprint.print_header()
    ffprint.print_info(ffinfo)
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
    if opt.copy_bitrate:
        opts.append("-b:v {}".format(ffinfo["bit_rate"]))
    else:
        opts.append("-profile:v high")
        if opt.profile_level is not None:
            opts.append(f"-level:v {opt.profile_level}")
        else:
            opts.append("-level:v {}".format(ffinfo["level"]))
    # -vf option
    vf_opt = []
    # -vf: scale
    if opt.scale is not None:
        vf_opt.append(f"scale={opt.scale}:-2")
    else:
        # only convert the scale if current scale is more than DEFAULT_SCALE.
        if ffinfo["width"] > _DEFAULT_SCALE:
            vf_opt.append(f"scale={_DEFAULT_SCALE}:-2")
    # -vf: rotation
    if opt.rotate is not None:
        if opt.rotate.lower() in ["r", "right"]:
            vf_opt.append("transpose=1")
        elif opt.rotate.lower() in ["l", "left"]:
            vf_opt.append("transpose=2")
        else:
            # just ignore it.
            pass
    if len(vf_opt):
        opts.append("-vf " + ",".join(vf_opt))
    # set ripping duration.
    # and, get parameters for progress bar.
    if (opt.time_start is None and opt.time_end is None and
        opt.time_duration is None):
        total_dur = get_duration(ffinfo)
    else:
        if opt.time_start:
            opts.append(f"-ss {opt.time_start}")
            time_start = parse_time(opt.time_start)
        else:
            time_start = 0
        #
        if opt.time_duration:
            # ignore even if --time-end is specified.
            opts.append(f"-t {opt.time_duration}")
            total_dur = time_start + parse_time(opt.time_duration)
        elif opt.time_end:
            opts.append(f"-to {opt.time_end}")
            total_dur = parse_time(opt.time_end) - time_start
        else:
            total_dur = get_duration(ffinfo) - time_start
    #
    opts = " ".join(opts)

    cmd = (f"ffmpeg -i {shlex.quote(input_file)} "
        f"{opts} "
        f"{shlex.quote(output_file)}")
    print("===>", cmd)
    print("Duration:", str(timedelta(seconds=total_dur)))
    p = Popen(shlex.split(cmd), stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
            universal_newlines=True
            )

    while True:
        buf = p.stderr.readline()
        if not buf:
            break
        if "Not overwriting" in buf:
            print("ERROR: output filename has exsted.")
            break
        # frame=  671 fps= 19 q=-1.0 Lsize=   63844kB time=00:06:01.49 bitrate=1446.8kbits/s dup=380 drop=387 speed=0.324x    
        if opt.verbose:
            print(buf, end="", flush=True)
        else:
            r = re.search(r"time=(\d+:\d+:\d+\.\d+) .*", buf)
            if r:
                progress_bar(parse_time(r.group(1)), total_dur)

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
                type=int,
                help="specify the size of x for scale. e.g. --scale 1280")
ap.add_argument("--rotate", action="store", dest="rotate",
                default=None, choices=["right", "r", "left", "l"],
                help="specify the direction of 90 rotation.")
ap.add_argument("-st", "--time-start", "--start-time",
                action="store", dest="time_start",
                help="pass the value to ffmpeg the -ss option.")
ap.add_argument("-et", "--time-end", "--end-time",
                action="store", dest="time_end",
                help="pass the value to ffmpeg the -to option.")
ap.add_argument("-dt", "--time-duration",
                action="store", dest="time_duration",
                help="pass the value to ffmpeg the -t option.")
ap.add_argument("-an", action="store_true", dest="no_audio",
                help="remove audio..")
ap.add_argument("-f", action="store_true", dest="force",
                help="force to convert the file.")
ap.add_argument("-R", action="store_false", dest="copy_bitrate",
                help="inform not to use original bitrate. "
                    "instead, use profile:high")
ap.add_argument("-y", action="store_true", dest="overwrite",
                help="overwrite the output file.")
ap.add_argument("-p", action="store_true", dest="show_profile",
                help="show only profile.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

# force ?
if set([opt.rotate, opt.scale, opt.time_start, opt.time_end, opt.time_duration,
        opt.no_audio, opt.profile_level]) != {False, None}:
    opt.force = True
    print("NOTE: set opt.force.")

##
if opt.input_file == ["-"]:
    for f in sys.stdin:
        do_main(f.strip())
else:
    for f in opt.input_file:
        do_main(f.strip())

