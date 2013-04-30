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
        return '\n'.join(self.__list__())

    def __list__(self):
        """Return sorted list of tree."""
        ls = []
        return self.getList(self.root, ls)
    
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

        #ancestor = root
        #lineage = []
        #while ancestor:
        #    if ancestor.parent:
        #        lineage.insert(0, ancestor.name)
        #    ancestor = ancestor.parent
        lineage = root.lineage()
        for f in root.files:
            ls.append('.'.join(lineage + [f,]))

        return ls


if __name__ == '__main__':
    i = Index()
    import pdb; pdb.set_trace()
