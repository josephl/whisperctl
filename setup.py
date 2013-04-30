from setuptools import setup

setup(
    name = 'whisperctl',
    version = '0.2.0',
    packages = ['whisperctl', 'whisperctl.indexer'],
    author = 'Joseph Lee',
    author_email = 'joseph@idealist.org',
    description = 'A tool for managing Whisper databases used in Graphite.',
    keywords = ['whisper', 'graphite', 'carbon', 'statsd'],
    url = 'http://github.com/josephl/whisperctl',
    license = 'MIT',
    scripts = ['scripts/whisperctl'],
    install_requires = ['whisper']
)
