from setuptools import setup

setup(
    name = 'whisperctl',
    version = '0.1',
    packages = ['whisperctl'],
    author = 'Joseph Lee',
    author_email = 'josephl@cecs.pdx.edu',
    description = ('A tool for managing Whisper databases used in '
        'Graphite. Wrappers for whisper-*.py scripts packaged '
        'with Whisper as well as regex and wildcard completion for '
        'managing multiple databases.'),
    url = 'http://github.com/josephl/whisperctl',
    license = 'MIT',
    scripts = ['scripts/whisperctl'],
    install_requires = ['whisper']
)
