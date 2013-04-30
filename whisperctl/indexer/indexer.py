import os
import re

class MetricPath:
    def __init__(self, parent, name, files):
        self.name = name
        self.parent = parent
        self.files = files
        self.children = None

    def adopt(self, children):
        self.children = children

    def lineage(self):
        line = [self.name,]
        ancestor = self.parent
        while ancestor:
            if ancestor.parent:
                line.insert(0, ancestor.name)
            ancestor = ancestor.parent
        return line

class Index:
    def __init__(self, storage='/opt/graphite/storage/whisper/'):
        self.storage = storage
        self.walk = os.walk(storage)
        self.root = self.create('', None, *self.walk.next())

    def __str__(self):
        return '\n'.join(list(self))

    def __iter__(self):
        """Return sorted list of tree."""
        ls = []
        for metric in self.getList(self.root, ls):
            yield metric
    
    def create(self, name, parent, curdir, subdirs, curfiles):
        newPath = MetricPath(parent,
                name,
                map(lambda x: re.sub('\.wsp$', '', x), curfiles))
        children = []
        for subdir in subdirs:
            children.append(self.create(subdir, newPath, *self.walk.next()))
        newPath.adopt(children)

        return newPath

    def getList(self, root, ls):
        for child in root.children:
            self.getList(child, ls)

        lineage = root.lineage()
        for f in root.files:
            ls.append('.'.join(lineage + [f,]))

        return ls


if __name__ == '__main__':
    i = Index()
