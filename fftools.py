import sys
from subprocess import Popen, PIPE, DEVNULL
import shlex
import math
import json
from datetime import timedelta
from shutil import get_terminal_size
import os

class ffPrintInfo():

    def __init__(self, print_mode=0, verbose=False):
        """
        print_mode: 0:short, 1:middle, 2:long
        """
        self.print_mode = print_mode
        self.verbose = verbose
        if print_mode == 0:
            self.hdrs = {
                    "str_duration": "Duration",
                    "fixed_filename": "Filename ",
                    }
        elif print_mode == 1:
            self.hdrs = {
                    "str_duration": "Duration",
                    "str_bit_rate": "Bitrate ",
                    "coded_width": "W   ",
                    "coded_height": "H   ",
                    "fixed_filename": "Filename ",
                    }
        else:
            self.hdrs = {
                    "str_duration": "Duration       ",
                    "str_bit_rate": "Bitrate ",
                    "coded_width": "W   ",
                    "coded_height": "H   ",
                    "aspect_ratio": "Aspect R.",
                    "profile": "Prof.",
                    "level": "Lv.",
                    "filesize": "Filesize   ",
                    "fixed_filename": "Filename ",
                    }
        #
        self.header_format = " ".join([f"{{:{len(i)}}}"
                                       for i in self.hdrs.values()])
        self.hdr_sep = " ".join([ "-"*len(i) for i in self.hdrs.values() ])
        self.left_cols_len = (len(self.hdr_sep) -
                              len(self.hdrs["fixed_filename"]) - 1)

    def print_header(self):
        print(self.header_format.format(*self.hdrs.values()))
        print(self.hdr_sep)

    def print_info(self, path, ffinfo):
        """
        ffinfo: output of get_stream_info()
        """
        def str_duration(duration):
            str_dur = str(timedelta(seconds=duration)).rjust(15,"0")
            if self.print_mode == 2:
                return str_dur[:15]
            else:
                return str_dur[:8]
        # get bit rate.
        def get_bitrate(ffinfo):
            """
            bps
            """
            br = ffinfo.get("bit_rate")
            if br is not None:
                return float(br)
            return ffinfo["filesize"]*8000000 / ffinfo["duration"]
        def str_bitrate(bitrate):
            """
            kbps
            """
            a, b = str(bitrate/1000).split(".")
            return "{}.{}".format(a.rjust(4," "), b[:3].ljust(3,"0"))
        # make profile name
        def get_profile(ffinfo):
            profile_map = {
                    "Constrained Baseline": "CBase",
                    "Baseline": "Base",
                    "Extended": "Ext",
                    "Multiview High": "MHigh",
                    "Stereo High": "SHigh",
                    }
            return profile_map.get(ffinfo["profile"], ffinfo["profile"])
        # fix filename
        def fix_filename(path):
            if self.print_mode == 2:
                return path
            else:
                name_len = (get_terminal_size((80,0)).columns -
                            self.left_cols_len - 1)
                return os.path.basename(path)[:name_len]
        #
        # set info
        #
        ffinfo["filesize"] = os.stat(path).st_size / 1000000  # MB
        ffinfo["duration"] = get_duration(ffinfo)
        ffinfo["str_duration"] = str_duration(ffinfo["duration"])
        # fileseize and duration must be set before bit_rate is set.
        ffinfo["bit_rate"] = get_bitrate(ffinfo)
        ffinfo["str_bit_rate"] = str_bitrate(ffinfo["bit_rate"])
        ffinfo["profile"] = get_profile(ffinfo)
        ffinfo["fixed_filename"] = fix_filename(path)
        ffinfo["aspect_ratio"] = get_aspect_ratio(ffinfo)
        #
        print(self.header_format.format(
                *[ffinfo[k] for k in self.hdrs.keys()]))

def get_duration(ffinfo):
    """
    ffinfo: json of ffprobe output.
    return the duration of the stream in seconds.
    mkv doesn't have duration, but does tags:DURATION.
    """
    duration = ffinfo.get("duration")
    if duration is not None:
        try:
            duration = float(duration)
        except Exception as e:
            return 0
        else:
            return duration
    # e.g. 00:03:20.720000000
    d = "00:00:00.000000000"
    str_dur = ffinfo.get("tags",{"DURATION":d}).get("DURATION",d)
    return sum([p*q for p,q in
                zip([float(i) for i in str_dur.split(":")],
                    [3600,60,1])])

def get_stream_info(input_file, codec_type=None, verbose=False):
    """
    codec_type: video, audio, or None
    """
    cmd = f"ffprobe -i {shlex.quote(input_file)} -v error -show_streams -of json"
    if verbose:
        print("COMMAND:", cmd)
    p = Popen(shlex.split(cmd), stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
            universal_newlines=True)
    ff_result, err = p.communicate()
    if err:
        raise ValueError("ERROR:", err)
    ffinfo = json.loads(ff_result)
    if verbose:
        print("\n".join([ "{}={}".format(*a) for a in ffinfo.items() ]))
    if codec_type is not None:
        ffinfo = [ x for x in ffinfo["streams"]
                   if x["codec_type"] == codec_type ]
    if len(ffinfo) == 0:
        print("ERROR: no stream info")
    # put filename in each dict.
    for x in ffinfo:
        x["filename"] = input_file
    return ffinfo

def get_aspect_ratio(ffinfo):
    ar = ffinfo.get("display_aspect_ratio")
    if ar is None:
        w = ffinfo["coded_width"]
        h = ffinfo["coded_height"]
        ar = ":".join([str(int(i/math.gcd(w, h))) for i in [w,h]])
    return ar

def get_frames(input_file, max_frames=0, entries=[], verbose=False):
    """
    entries:
        "media_type", "stream_index", "key_frame",
        "pkt_pts", "pkt_pts_time", "pkt_dts", "pkt_dts_time",
        "best_effort_timestamp", "best_effort_timestamp_time",
        "pkt_duration", "pkt_duration_time", "pkt_pos",
        "pkt_size", "width", "height", "pix_fmt",
        "sample_aspect_ratio", "pict_type", "coded_picture_number",
        "display_picture_number", "interlaced_frame", "top_field_first",
        "repeat_pict", "color_range", "color_space", "color_primaries",
        "color_transfer", "chroma_location",
    """
    opts = ["-v error -of compact -select_streams v -show_frames"]
    if entries:
        opts.append("-show_entries frame={}".format(",".join(entries)))
    opts.append(f"-i {shlex.quote(input_file)}")
    cmd = "ffprobe {}".format(" ".join(opts))
    if verbose:
        print("CMD==>", cmd)
    #
    frames = []
    p = Popen(shlex.split(cmd), stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    nb_lines = 1
    while p.poll() is None:
        cols = p.stdout.readline().strip().split("|")
        if verbose:
            print("COL:", cols)
        if cols[0] != "frame":
            # it's not a frame info, just to be ignored.
            continue
        frames.append(dict(x.split("=") for x in cols[1:]))
        # another condition to break
        nb_lines += 1
        if max_frames and nb_lines > max_frames:
            break

    if p.poll():
        print(f"ERROR: {p.stderr.read()}")

    return frames

def parse_time(src):
    """
    convert time-like string into a float number in second.
    return the number.
    """
    if src.find(".") > 0:
        s_hms, s_dec = src.split(".")
        n_dec = float(f".{s_dec.ljust(6,'0')}")
    else:
        s_hms = src
        n_dec = 0.
    s = s_hms.replace(":","").rjust(6,"0")
    return sum([a*b for a,b in zip(
            [int(s[i:i+2]) for i in range(0,6,2)],
            [3600,60,1])]) + n_dec

def progress_bar(a, b, width=70):
    # "[" + "="*width + "]"
    if b != 0:
        bar = "="*int(a/b*width)
        sys.stdout.write("\r[{}] {:3}%".format(bar.ljust(width), int(a/b*100)))
    else:
        sys.stdout.write("\r[{}] {:3}%".format("="*width, "???"))
    if a == b:
        sys.stdout.write("\n")
    sys.stdout.flush()

