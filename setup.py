from setuptools import setup

setup(
    name = 'whisperctl',
    version = '0.1.1',
    packages = ['whisperctl'],
    author = 'Joseph Lee',
    author_email = 'josephl@cecs.pdx.edu',
    description = 'A tool for managing Whisper databases used in Graphite.',
    keywords = ['whisper', 'graphite', 'carbon', 'statsd'],
    url = 'http://github.com/josephl/whisperctl',
    license = 'MIT',
    scripts = ['scripts/whisperctl'],
    install_requires = ['whisper']
)
