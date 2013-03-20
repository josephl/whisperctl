#!/usr/bin/env python

import subprocess
from datetime import datetime
from time import time
import re
from sys import argv
import os

try:
    metric = argv[1]
except IndexError:
    raise IndexError('Please specify metric')

dump = '/opt/graphite/bin/whisper-dump.py'
baseDir = '/opt/graphite/storage/whisper'
whisperPath = os.path.join(baseDir, metric.replace('.', '/') + '.wsp')

cmd = [dump, whisperPath]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
lineCount = 0

for line in p.stdout:
    m = re.match('[0-9]+:[ \t]*(?P<name>[1-9][0-9]*),'
                 '[ \t]*(?P<val>([1-9][.0-9]*)|(0[.][0-9]*))', line)
    if m:
        d = m.groupdict()
        print '%s - %s' % (datetime.fromtimestamp(float(d['name'])),
                                d['val'])
        lineCount += 1
print '-----\n%d non-null observations' % (lineCount)
