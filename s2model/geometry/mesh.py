# (c) 2011 savagerebirth.com
# (c) 2023 DRX Dev Team

from .vectors import Vec3

class Mesh:
	NAME_LENGTH = 32
	def __init__(self):
		self.name = "_mesh"
		self.texture = "null.tga" #one mesh per texture? or vice versa
		self.numVerts = 0
		self.verts = []
		self.numFaces = 0
		self.faces = []
		self.boneLink = -1 #rigid mesh
		self.bmin = Vec3(0.0,0.0,0.0)
		self.bmax = Vec3(0.0,0.0,0.0)
		self.blend = False
	
	def calcBBox(self):
		pass
