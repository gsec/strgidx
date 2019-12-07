#!/usr/bin/env python
# encoding: utf-8
# HDD Directory snapshot <idd-script by gsec(2016)>
# create a quick index of a disk along with most important metadata.

import arrow
import argparse
import logging
from subprocess import Popen, PIPE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

""" We get the device info from either the dev or the mount point.

Those we get with `blkid` or `findmnt` which we open with subprocess. The weird piping is
necessary to get the output rather than exit code from programs.
"""

def findmount(dir):
    """ Create a dict with source and target from any of them through `findmnt`
    """
    # get infos from findmnt about paths and such
    fnd =  Popen(['findmnt', dir], stdout=PIPE)
    stdout, stderr = fnd.communicate()
    ks, vs = str(stdout, 'utf-8').strip().split('\n')
    DICT = dict(zip(ks.split(), vs.split()))

    # additional infos thourgh blkid
    p =  Popen(['blkid', DICT['SOURCE']], stdout=PIPE)
    stdout, stderr = p.communicate()
    text = str(stdout, 'utf-8').strip().split()[1:]
    blk_dic = {k: v.strip('\"') for pair in text for k, v in [pair.split('=')]}
    # blk_dic.pop('TYPE')

    #merge both
    DICT.update(blk_dic)

    return DICT


def tree_string(path):
    t = Popen(['tree', '-d', path], stdout=PIPE)
    stdout, stderr = t.communicate()
    return str(stdout, 'utf-8')


def main():
    parser = argparse.ArgumentParser(prog='idd')
    parser.add_argument('device', help="Specify device or mountpoint!")
    parser.add_argument("--output", "-o", default=None, nargs='?',
                        help="Output file for the index")

    args = parser.parse_args()
    meta = findmount(args.device)
    meta['TIMESTAMP'] = arrow.now().isoformat()
    greeting = "HDD Directory snapshot <idd-script by gsec(2016)>\n\n"

    logger.info(meta)

    if not args.output:
        try:
            meta['LABEL']
        except KeyError:
            meta['LABEL'] = input(
                "Please enter a label for the device {} : ".format(args.device))
        args.output = '{}_{}.{}'.format(meta['LABEL'],
                                        meta['TIMESTAMP'].split('T')[0],
                                        'tree')
    with open(args.output, '+x') as f:
        f.write(greeting)
        for k ,v in meta.items():
            f.write("{key: <{fill}}:: {val}\n".format(key=k, val=v, fill=10))
        f.write('\n' + tree_string(meta['TARGET']))
    logger.info("HDD index created at {}".format(args.output))


if __name__ == '__main__':
    main()
