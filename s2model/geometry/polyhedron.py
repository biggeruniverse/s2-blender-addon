# (c) 2011 savagerebirth.com

from .vectors import Vec3;

__all__ = ["Plane", "Polyhedron"]

class Plane:
        def __init__(self, n, d):
            self.normal = n;
            self.dist = d;

class Polyhedron:
        FLAGS [ '0', 't', 'T', 'D', 'e', 'C', 'G', 's', 'F', '0', '1', '2', '3', 'S', 'r', 'o', 'p', 'R', '4', '5', '6', '7', 'L', 'c'];
        def __init__(self):
            self.name = "_surf0_";
            self.numPlanes = 0;
            self.planes = [];

        def setFlags(self, f):
            for i in len(Polyhedron.FLAGS):
                mask = 1<<i;
                if f & mask == mask:
                    self.name += Polyhedron.FLAGS[i];

        def getFlags(self):
            flags = 0;
            #TODO
            return flags;

        def convertToMesh(self):
            pass;
