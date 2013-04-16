#!/usr/bin/env python

# whisperctl
# Tools to make your graphite life easier
# Wrappers for the whisper-*.py scripts which allow for
# metrics to be specified as they are in graphite
# tools: index, search, info, dump

import os
import subprocess
import re
import sys
import logging
from datetime import datetime
import ConfigParser


config = ConfigParser.SafeConfigParser()
config.read('whisperctl.conf')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

whisper_root = config.get('whisper', 'PATH')
index_file = config.get('whisper', 'INDEX')

bins = {
    'info': config.get('whisper', 'INFO'),
    'dump': config.get('whisper', 'DUMP'),
    'resize': config.get('whisper', 'RESIZE')
}


def index(*args):
    """
    Walk through whisper tree, store sorted list of metrics by converting
    file structure to graphite metric naming conventions
    """
    wwalk = os.walk(whisper_root)
    metrics = []

    for d in iter(wwalk):
        pathto = d[0].replace(whisper_root, '', 1).lstrip('/')
        for f in d[2]:
            match = re.match('^(.*)[.]wsp$', f)
            if match is not None:
                fname = match.group(1)
                metrics.append(
                    os.path.join(pathto,
                        fname).replace('/', '.') + '\n')
    #metrics.sort()
    with open(index_file, 'w') as ifd:
        ifd.writelines(metrics)

def search(*args):
    """
    Run regex search on whisper index for metrics
    args: regex pattern(s). Accetps regex string or iterable of regexs
    returns the union of all matches for each pattern given
    """
    if hasattr(args, '__iter__'):
        patterns = args
    else:
        patterns = [args,]
    metrics = []
    with open(index_file, 'r') as ifd:
        indexes = ifd.readlines()
    for line in indexes:
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                logger.info('    %s' % (line.strip()))
                metrics.append(line.strip())
    metrics = set(metrics)
    return metrics

def info(*args):
    """
    Wrapper for `whisper-info.py metric`
    """
    metricInfo = { 'archives': [] }
    metric = args[0]

    cmd = [bins['info'], metric_path(metric)]
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    info = s.stdout.read()
    for stanza in info.strip().split('\n\n'):
        if stanza.startswith('Archive'):
            archive = {}
            for line in stanza.split('\n'):
                if ':' in line:
                    key, val = map(lambda s: s.strip(), line.split(':'))
                    archive.update({ key: val })
            metricInfo['archives'].append(archive)
        else:
            for line in stanza.split('\n'):
                if ':' in line:
                    key, val = map(lambda s: s.strip(), line.split(':'))
                    metricInfo.update({ key: val })
    logger.info(metricInfo)
    return metricInfo


def findall(path):
    """
    return list of all metrics that start with path
    """
    return search('^%s\.' % (path))


def dump(*args):
    """
    Wrapper for `whisper-dump.py metric`
    Dumps all null values
    """
    metric = args[0]
    cmd = [bins['dump'], metric_path(metric)]
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pattern = '^[0-9]+:[ \t]+(?P<date>[1-9][0-9]*),'\
        '[ \t]+(?P<val>(-){0,1}([1-9][0-9]+|0[.][0-9]*))$'
    dateRange = { 'min': None, 'max': None }
    for line in s.stdout:
        m = re.match(pattern, line)
        if m:
            d = m.groupdict()
            date = int(d['date'])
            #logger.info('%s  |  %s' % (
            #    datetime.fromtimestamp(date), d['val']))
            if (dateRange['min'] is None or
                   date < dateRange['min']):
                dateRange['min'] = date
            if (dateRange['max'] is None or
                   date > dateRange['max']):
                dateRange['max'] = date
    logger.info(' Range of dates: (%s, %s)' % (
                datetime.fromtimestamp(dateRange['min']),
                datetime.fromtimestamp(dateRange['max'])))

def resize(*args):
    """
    Wrapper for whisper-resize.py
    """
    cmd = list(args)
    cmd[0] = metric_path(cmd[0])
    cmd.insert(0, bins['resize'])
    try:
        s = subprocess.check_call(cmd)
    except IOError as ioe:
        raise ioe
    except subprocess.CalledProcessError as cpe:
        raise cpe

def xff(*args):
    """
    args: (metric, xFilesFactor)
    xFilesFactor is a float within range [0, 1]

    You can't just change the xFilesFactor of a metric using whisper-resize
    without respecifying the retention rates of the metric. This method
    allows you to do so by only supplying the xFilesFactor value.
    """
    metric = args[0]
    xffVal = args[1]
    ret = []
    logger.info(info(metric)['archives'])
    for archive in info(metric)['archives']:
        ret.append('%s:%s' % (archive['secondsPerPoint'],
                              archive['points']))
    resizeCmd = [metric, '--xFilesFactor=%s' % (xffVal)]
    resizeCmd += ret
    print resizeCmd
    resize(*resizeCmd)

def metric_path(metric):
    """
    Determine path for metric in '.' form or determine if supplied
    metric name is already a valid path
    """
    return os.path.join(whisper_root,
                        '%s.wsp' % (metric.replace('.', os.path.sep)))

options = {
    'index': index,
    'search': search,
    'info': info,
    'resize': resize,
    'xff': xff,
    'dump': dump
}

def main():
    from sys import argv
    try:
        options[argv[1]](*argv[2:])
    except:
        print """
        whisperctl commands
        -------------------
            index       update whisper index
            search      regex search of index for metrics
            info        print whisper metric information
            resize      change data retentions for metric
            dump        print whisper database values to stdout
        """
        raise


if __name__ == '__main__':
    main()
