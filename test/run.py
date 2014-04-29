#! /usr/bin/python
# EASY-INSTALL-ENTRY-SCRIPT: 'nose==1.3.1','console_scripts','nosetests'
__requires__ = 'nose'
import pybble # for monkeypatching
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('nose', 'console_scripts', 'nosetests')()
    )
