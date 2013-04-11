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


class WhisperCtl:

    def __init__(self, root='/opt/graphite', whisper='storage/whisper',
                 bins=None):
        self.root = root
        self.storage = os.path.join(root, whisper)
        self.indexFile = os.path.join(root, 'storage/index')
        if not bins:
            self.bins = {
                'info': os.path.join(self.root, 'bin', 'whisper-info.py'),
                'dump': os.path.join(self.root, 'bin', 'whisper-dump.py'),
                'resize': os.path.join(self.root, 'bin',
                                       'whisper-resize.py'),
            }
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def index(self, *args):
        '''
        Walk through whisper tree,
        store sorted list of metrics by converting file structure
        to graphite naming conventions
        '''
        wwalk = os.walk(self.root)
        indexes = []

        for d in iter(wwalk):
            pathto = d[0].replace(self.storage, '').lstrip('/')
            for f in d[2]:
                match = re.match('^(.*)[.]wsp$', f)
                if match is not None:
                    fname = match.group(1)
                    indexes.append(
                        os.path.join(pathto,
                            fname).replace('/', '.') + '\n')
        indexes.sort()
        try:
            ifd = open(self.indexFile, 'w')
            ifd.writelines(indexes)
            ifd.close()
        except IOError as ioe:
            raise ioe 

    def search(self, *args):
        '''
        Run regex search on whisper index for string
        args: regex pattern
        '''
        pattern = args[0]
        matches = []
        try:
            ifd = open(self.indexFile, 'r')
            indexes = ifd.readlines()
            ifd.close()
            for line in indexes:
                match = re.search(pattern, line)
                if match:
                    self.logger.info(line.strip())
                    matches.append(line.strip())
        except IOError as ioe:
            raise ioe
        #print '-----\n%d matches found' % len(matches)
        return matches

    def info(self, *args):
        '''
        Wrapper for `whisper-info.py metric`
        '''
        metricInfoList = []
        metrics = self.parseMetricWC(args)
        if not metrics:
            metrics = self.parseMetricExp(args)
        for metric in metrics:
            cmd = [self.bins['info'], self.metricPath(metric)]
            # run cmd
            s = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            metricInfo = s.stdout.read()
            self.logger.info('\n%s' %(metric))
            self.logger.info(('-' * len(metric)))
            self.logger.info(metricInfo.strip())
            metricInfoList.append(metricInfo)
        return metricInfoList

    
    def findall(self, path):
        '''
        return list of all metrics that start with path
        '''
        return self.search('^%s[.]' %(path))


    def dump(self, *args):
        '''
        Wrapper for `whisper-dump.py metric`
        Dumps all null values
        '''
        metric = args[0]
        cmd = [self.bins['dump'], self.metricPath(metric)]
        s = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        pattern = '^[0-9]+:[ \t]+(?P<date>[1-9][0-9]*),'\
            '[ \t]+(?P<val>(-){0,1}([1-9][0-9]+|0[.][0-9]*))$'
        dateRange = { 'min': None, 'max': None }
        for line in s.stdout:
            m = re.match(pattern, line)
            if m:
                d = m.groupdict()
                date = int(d['date'])
                self.logger.info('%s  |  %s' % (
                    datetime.fromtimestamp(date), d['val']))
                if dateRange['min'] is None or\
                   date < dateRange['min']:
                    dateRange['min'] = date
                if dateRange['max'] is None or\
                   date > dateRange['max']:
                    dateRange['max'] = date
        self.logger.info('-----\nRange of dates:')
        self.logger.info('(%s, %s)' % (
            datetime.fromtimestamp(dateRange['min']),
            datetime.fromtimestamp(dateRange['max'])))

    def resize(self, *args):
        '''
        Wrapper for whisper-resize.py
        '''
        cmd = list(args)
        cmd[0] = self.metricPath(cmd[0])
        cmd.insert(0, self.bins['resize'])
        try:
            s = subprocess.check_call(cmd)
        except IOError as ioe:
            raise ioe
        except subprocess.CalledProcessError as cpe:
            raise cpe

    def xff(self, *args):
        '''
        args: (metric, xFilesFactor)
        xFilesFactor is a float within range [0, 1]

        Change the xFilesFactor of a metric
        This is a pain to accomplish in a sane manner without a tool.
        whisper-resize.py must be used with a command-line option of
        '--xFilesFactor=#' but you cannot do it without supplying
        time retention rates. That means you have to re-enter the
        existing retention rates if you don't want them to change,
        and there is no way to get current retention rates in a
        a similar format that the input requires. wtf
        '''
        try:
            metric = self.metricPath(args[0])
            xffVal = args[1]
        except:
            raise
        metricInfoList = []
        metricInfoList = self.info(metric)
        for metricInfo in metricInfoList:
            metricStanzas = metricInfo.strip().split('\n\n')
            ret = []    # time retentions
            for ms in metricStanzas[1:]:
                match = re.search('secondsPerPoint: ([0-9]*)\n'\
                                  'points: ([0-9]*)', ms)
                if match:
                    spp, pts = map(int, match.groups())
                    s = '%d:%d' %(spp, pts)
                    ret.append(s)
            resizeCmd = [metric, '--xFilesFactor=' + xffVal]
            resizeCmd += ret
            self.resize(*resizeCmd)
        

    def metricPath(self, *args):
        '''
        Determine path for metric in '.' form or determine if supplied
        metric name is already a valid path
        '''
        metric = args[0]
        if metric.count(os.path.sep) > 0 and metric.endswith('.wsp'):
            if metric.startswith(self.root):
                return metric
            else:
                return os.path.join(self.storage, metric)
        return os.path.join(self.storage,
            metric.replace('.', os.path.sep) + '.wsp');

    def parseMetricExp(self, args):
        '''
        determine metric or metrics if '-e' flag for reg expression is set
        '''
        metrics = []
        if args[0] == '-e':
            args = args[1:]
            pattern = args[0]
            metrics = self.search(pattern)
        else:
            metrics.append(args[0])
        return metrics

    def parseMetricWC(self, args):
        '''
        allow for wildcard completion. only accepts wildcard as a suffix
        '''
        if args[0].endswith('*'):
            pattern = '^%s.*$' %(args[0].replace('.', '[.]'))
            metrics = self.search(pattern)
            return metrics
        else:
            return None

    def runTool(self, tool, args):
        try:
            getattr(self, tool)(*args)
        except TypeError as te:
            raise te

        
if __name__ == '__main__':
    from sys import argv
    wc = WhisperCtl()
    try:
        tool = argv[1]
        args = argv[2:]
    except:
        print '''
whisperctl commands
-------------------
    index       update whisper index.
    search      regex search of index for metrics
    info        print whisper metric information
    resize      change data retentions for metric
    xff         change xFilesFactor value for metric

    you may search for matching metric names using '-e pattern' instead
    of a metric name
    wildcard suffixes can also be matched:
    i.e.    whisperctl info "stats.test.*"
    '''
        raise IndexError('whisperctl <tool> [<metric>]')

    try:
        wc.runTool(tool, args)
    except AttributeError as ae:
        print ae
        raise AttributeError('Invalid option: \'%s\'' %(tool))
    except:
        raise
