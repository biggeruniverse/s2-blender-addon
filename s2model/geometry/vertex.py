# (c) 2011 savagerebirth.com
# (c) 2023 DRX Dev Team

from .vectors import Vec3

class Color4:
        def __init__(self):
                self.data = [1.0,1.0,1.0,1.0]

class Vertex(Vec3):
        def __init__(self):
                Vec3.__init__(self,0.0,0.0,0.0)
                self.color = Color4()
                self.normal = Vec3(0.0,1.0,0.0)
                self.texcoord = [0.0, 0.0]
