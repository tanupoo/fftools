import sys
from subprocess import Popen, PIPE, DEVNULL
import shlex
import math
import json

def get_stream_info(input_file, codec_type=None, verbose=False):
    """
    codec_type: video, audio, or None
    """
    cmd = f"ffprobe -i {shlex.quote(input_file)} -v error -show_streams -of json"
    if verbose:
        print("COMMAND:", cmd)
    p = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE, stdin=DEVNULL,
            universal_newlines=True)
    ff_result, err = p.communicate()
    if err:
        raise ValueError("ERROR:", err)
    ff_info = json.loads(ff_result)
    if verbose:
        print("\n".join([ "{}={}".format(*a) for a in ff_info.items() ]))
    if codec_type is not None:
        ff_info = [ x for x in ff_info["streams"]
                   if x["codec_type"] == codec_type ]
    if len(ff_info) == 0:
        print("ERROR: no stream info")
    return ff_info

def get_aspect_ratio(a, b):
    return int(a/math.gcd(a,b)), int(b/math.gcd(a,b))

def progbar(a, b, width=60):
    # "[" + "="*width + "]"
    bar = "="*int(a/b*width)
    sys.stdout.write("\r[{}] {:3}% {}/{}".format(bar.ljust(width),
                                                 int(a/b*100), a,b))
    if a == b:
        sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    import time, random
    a = 0
    while a < 5000:
        a += random.randint(10,200)
        progbar(a,5000)
        time.sleep(.1)
    progbar(5000,5000)
