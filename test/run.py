#!/usr/bin/env python

# need to load pybble at the very beginning because it monkeypatches the
# threading module and everybody under the sun uses that thing
import pybble

# Then, just call nose
from nose.core import run
run()
