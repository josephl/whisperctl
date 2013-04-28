#!/usr/bin/env python

# whisperctl
# Tools to make your graphite life easier
# Wrappers for the whisper-*.py scripts which allow for
# metrics to be specified as they are in graphite
# tools: index, search, info, dump

from datetime import datetime
from argparse import ArgumentParser
import subprocess
import os
import re
#import logging
#import ConfigParser

#config = ConfigParser.SafeConfigParser()
#config.read('whisperctl.conf')
#
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

# default configs
graphite_root = '/opt/graphite'
whisper_root = os.path.join(graphite_root, 'storage/whisper')
bins = {
    'info': os.path.join(graphite_root, 'bin/whisper-info.py'),
    'dump': os.path.join(graphite_root, 'bin/whisper-dump.py'),
    'resize': os.path.join(graphite_root, 'bin/whisper-resize.py'),
    'agg': os.path.join(
        graphite_root, 'bin/whisper-set-aggregation-method.py')
}


def index(**kwargs):
    """
    Walk through whisper tree, store sorted list of metrics by converting
    file structure to graphite metric naming conventions.
    Return list if all metrics in graphite format.
    """
    wwalk = os.walk(whisper_root)
    #metric = kwargs['metric']

    metrics = []
    for d in iter(wwalk):
        pathto = d[0].replace(whisper_root, '', 1).lstrip('/')
        for fname in d[2]:
            if fname.endswith('.wsp'):
                metricName = re.sub('\.wsp$', '', os.path.join(
                        pathto, fname).replace('/', '.'))
                metrics.append(metricName)

    # Write out metrics to index file
    #with open(index_file, 'w') as ifd:
    #    ifd.write('\n'.join(metrics))

    return metrics

def search(**kwargs):
    """
    Run regex search on whisper index for metrics
    args: regex pattern(s). Accetps regex string or iterable of regexs
    returns the union of all matches for each pattern given
    """
    metric = kwargs['metric']
    metrics = []

    if kwargs['regex']:
        for i in index():
            if re.search(metric, i):
                metrics.append(i)
    elif '*' in metric:
        # Convert non-regex with wildcard to regex.
        metric = re.escape(metric)
        metric = metric.replace('\*', '[^.]*')
        for i in index():
            if re.search(metric, i):
                metrics.append(i)
    else:
        # non-regex
        if metric in index():
            metrics.append(metric)

    return metrics


def info(**kwargs):
    """
    Wrapper for `whisper-info.py metric`
    Only works for singular, explicit metric, no regex, wildcards.
    """
    metricInfo = { 'archives': [] }
    metric = kwargs['metric']

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
    #logger.info(metricInfo)
    return metricInfo


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
    #logger.info(' Range of dates: (%s, %s)' % (
    #            datetime.fromtimestamp(dateRange['min']),
    #            datetime.fromtimestamp(dateRange['max'])))

def resize(**kwargs):
    """
    Wrapper for whisper-resize.py
    """
    ret = kwargs['params']
    for metric in search(**kwargs):
        fname = metric_path(metric)
        cmd = [bins['resize'], fname] + ret

        try:
            s = subprocess.check_call(cmd)
        except IOError as ioe:
            raise ioe
        except subprocess.CalledProcessError as cpe:
            raise cpe

        try:
            os.remove('%s.bak' %(fname))
        except OSError:
            pass

def xff(**kwargs):
    """
    args: (metric, xFilesFactor)
    xFilesFactor is a float within range [0, 1]

    You can't just change the xFilesFactor of a metric using whisper-resize
    without respecifying the retention rates of the metric. This method
    allows you to do so by only supplying the xFilesFactor value.
    """
    xffVal = kwargs['params'][0]
    for metric in search(**kwargs):
        ret = []
        fname = metric_path(metric)
        #logger.info(info(metric)['archives'])
        for archive in info(metric=metric)['archives']:
            ret.append('%s:%s' % (archive['secondsPerPoint'],
                                  archive['points']))
        resizeCmd = [   bins['resize'],
                        fname,
                        '--xFilesFactor=%s' % (xffVal)  ] + ret

        try:
            s = subprocess.check_call(resizeCmd)
        except IOError as ioe:
            raise ioe
        except subprocess.CalledProcessError as cpe:
            raise cpe

        try:
            os.remove('%s.bak' %(fname))
        except OSError:
            pass

def agg(**kwargs):
    """
    Wrapper for whisper-set-aggregation-method.py
    """
    aggMethod = kwargs['params'][0]
    for metric in search(**kwargs):
        fname = metric_path(metric)
        cmd = [bins['agg'], fname, aggMethod]

        try:
            s = subprocess.check_call(cmd)
        except IOError as ioe:
            raise ioe
        except subprocess.CalledProcessError as cpe:
            raise cpe

        try:
            os.remove('%s.bak' %(fname))
        except OSError:
            pass


def metric_path(metric):
    """
    Determine path for metric in '.' form or determine if supplied
    metric name is already a valid path
    """
    if '/' in metric:
        if os.path.exists(metric):
            return metric
        elif os.path.exists('%s.wsp' % (metric)):
            return '%s.wsp' % (metric)
    return os.path.join(whisper_root,
                        '%s.wsp' % (metric.replace('.', os.path.sep)))

def main():
    commands = ['index', 'search', 'info', 'resize', 'xff', 'dump', 'agg']
    parser = ArgumentParser()
    parser.add_argument('command',
                        metavar='COMMAND',
                        choices=commands)
    parser.add_argument('-e', dest='regex', action='store_true',
                        help='METRIC is a regex')
    parser.add_argument('metric',
                        metavar='METRIC',
                        nargs='?')
    parser.add_argument('params',
                        metavar='PARAM',
                        nargs='*')
    args = parser.parse_args()

    print globals()[args.command](**args.__dict__)


if __name__ == '__main__':
    main()
