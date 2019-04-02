#!/usr/bin/env python3

import argparse
import os
import errno
import sys
import shutil
from ida.css.wfdisc import WfdiscFile

def main():
    
    # for line in sys.stdin:
    #     sys.stdout.write('out: ' + line)

    wfd = WfdiscFile('/Users/dauerbach/dev/dcc/dcc-modules-py/ida/css/tests/data/TKL_ALL.20170308.0000.wfdisc')
    
    wfd.write_miniseed('testout.ms', 'II')
    with open('testout.ms', 'rb') as msin:
        while True:
            block = msin.read(2^20)
            if block:
                sys.stdout.buffer.write(block)
            else:
                break
    os.unlink('testout.ms')

if __name__ == '__main__':
    main()
