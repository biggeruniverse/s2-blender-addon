# (c) 2011 savagerebirth.com
# (c) 2023-2026 DRX Dev Team

from .vectors import Vec3

class Mesh:
	NAME_LENGTH = 32
	TEX_NAME_LENGTH = 64

	def __init__(self):
		self.name = "_mesh"
		self.texture = "null.tga" #one mesh per texture? or vice versa
		self.numVerts = 0
		self.verts = []
		self.numFaces = 0
		self.faces = []
		self.boneLink = -1 #rigid mesh
		self.bmin = Vec3(1000000.0,1000000.0,1000000.0)
		self.bmax = Vec3(-1000000.0,-1000000.0,-1000000.0)
		self.blend = False
		self.mode = 0 # MESH_UNSKINNED
	
	def calcBBox(self):
		pass
