import os
import sys

class Mute:

    def __enter__(self):
        self.realso = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, *args):
        sys.stdout.close()
        sys.stdout = self.realso
