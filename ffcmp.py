#!/usr/bin/env python

import sys
import json
from fftools import get_stream_info
import argparse

# get common keys.
def get_common_keys(dict_list, shallow=True, ignore_keys=None):
    """
    it keeps keys order as much as possible.
    the fist one in dict_list is used as a base.
    """
    if len(dict_list) == 0:
        return []
    keys = []
    for dct in dict_list:
        for i,kv in enumerate(dct.items()):
            if isinstance(kv[1], (dict, list)):
                continue
            if kv[0] in ignore_keys:
                continue
            if kv[0] in keys:
                continue
            keys.insert(i,kv[0])
    return keys

def show_dicts(*dicts, ignore_keys=None, only_diffs=False,
               target=None):
    """
    a0, b0: a dict, not a list.
        all key and value pairs must be formed like key : a value.
        any value must not be a list or dict.
    """
    if target is not None:
        if not isinstance(target, list):
            raise ValueError("ERROR: target must be a list.")
        # reconstruct the dicts.
        dicts = [ dicts[i] for i in target ]
    keys = get_common_keys(dicts, ignore_keys=ignore_keys)
    max_key_len = max([len(k) for k in keys])
    max_val_len = []
    for dct in dicts:
        max_val_len.append(max([len(str(v))
                                for k,v in dct.items()
                                if k in keys ]))
    # show table
    for k in keys:
        line = [ f"{k.ljust(max_key_len)}" ]
        # adding Diff Flag.
        for dct in dicts:
            if k not in dct:
                # the key doesn't exist, but does in any other dict.
                line.append("X")
                break
        else:
            # now the key exists in all the dicts.
            for dct in dicts[1:]:
                if dicts[0][k] != dct[k]:
                    line.append("X")
                    break
            else:
                # all the values are same.
                line.append(" ")
        #
        for i,dct in enumerate(dicts):
            if k in dct:
                line.append(str(dct[k]).ljust(max_val_len[i]))
            else:
                line.append(' '.ljust(max_val_len[i]))
        #
        print(" ".join(line))

ap = argparse.ArgumentParser(
        description="this is example.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="+", help="movie file.")
ap.add_argument("-t", action="store", dest="_target",
                help="specify the target to be compared, "
                "0 origin, comma separated.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="verbose mode.")
opt = ap.parse_args()

opt.target = None
if opt._target is not None:
    opt.target = [int(i) for i in opt._target.split(",")]

show_dicts(*[ get_stream_info(f,
                              codec_type="video",
                              verbose=opt.verbose)[0]
             for f in opt.input_file ],
           ignore_keys=["codec_long_name"],
           target=opt.target)
