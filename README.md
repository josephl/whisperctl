WhisperCtl
==========

A tool for managing [Whisper](http://github.com/graphite-project/whisper) databases used in [Graphite](http://github.com/graphite-project/graphite-web).

This script serves as a wrapper for the whisper-*.py scripts in the whisper package. Additionally, it can index and search Graphite metrics with regular expressions using the `-e` option flag or with wildcard completion.

The `xff` command allows for changing the xFilesFactor of metrics without having to reiterate the retention levels as `whisper-resize.py` requires.

## Setup

Recommended installation of WhisperCtl within a virtualenv:

```
pip install whisperctl
```

## Run
```
usage: whisperctl [-h] [-e] COMMAND [METRIC] [PARAM [PARAM ...]]

positional arguments:
  COMMAND
  METRIC
  PARAM

optional arguments:
  -h, --help  show this help message and exit
  -e          METRIC is a regex
  
Examples:
whisperctl xff carbon.*.counters.* 0.0
whisperctl agg carbon.*.timers.*.count sum
whisperctl -e search '.*'
```

