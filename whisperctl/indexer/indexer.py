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

    def dictify(self):
        return {
            'name': self.name,
            'files': self.files,
            'children': map(lambda c: c.dictify(), self.children)
        }


class Index:
    def __init__(self, storage='/opt/graphite/storage/whisper/'):
        self.storage = storage
        self.walk = os.walk(storage)
        self.root = self.create('', None, *self.walk.next())

    def __str__(self):
        return '\n'.join([m for m in list(self)])

    def __iter__(self):
        """Return sorted list of tree."""
        return self.getList(self.root)
    
    def create(self, name, parent, curdir, subdirs, curfiles):
        # filter curfiles for improper filenames w/ a '.'
        curfiles = filter(lambda y: '.' not in y,
                map(lambda x: re.sub('\.wsp$', '', x), curfiles))
        newPath = MetricPath(parent, name, curfiles)
        children = []
        for subdir in subdirs:
            children.append(self.create(subdir, newPath, *self.walk.next()))
        newPath.adopt(children)

        return newPath

    def getList(self, root):
        for child in root.children:
            for i in self.getList(child):
                yield i

        lineage = root.lineage()
        for f in root.files:
            yield '.'.join(lineage + [f,])

    def dictify(self):
        return self.root.dictify()

    def jsonify(self):
        import json
        return json.dumps(self.dictify())

if __name__ == '__main__':
    i = Index()
    di = i.dictify()
