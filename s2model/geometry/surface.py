# (c) 2011 savagerebirth.com
# (c) 2023 DRX Dev Team

from .vectors import Vec3
from .mesh import Mesh
from .face import Face
from .vertex import Vertex

S2_SURF_SIZE_HALF = .05

class line_t:
	def __init__(self):
		self.a = Vec3(0.0, 0.0, 0.0)
		self.x0 = Vec3(0.0, 0.0, 0.0)
		self.x1 = None
		
	def intersection(self, b):
		da = self.x1 - self.x0
		db = b.x1 - b.x0
		dc = b.x0 - self.x0
		
		if dc * da.cross(db) != 0.0:
			return None
		
		c = da.cross(db)
		if c.size2() == 0.0:
                        return None
		s = (dc.cross(db) * c) / c.size2()
		
		if s >= 0.0 and s <= 1.0:
			return self.x0 + da * s
			
		return None

	def __str__(self):
                return str(self.x0) + " to " + str(self.x1)

class plane_t:
	def __init__(self):
		self.distance = 0
		self.normal = Vec3(0.0, 0.0, 0.0)

class surface_t:
	#pertinent flags
	SURF_EX0               = 256
	SURF_EX1               = 512
	SURF_EX2               = 1024
	SURF_EX3               = 2048
	SURF_SOLID_ITEM        = 4096
	SURF_TRANSPARENT_ITEM  = 8192
	SURF_PUSH_ZONE         = 32768
	SURF_LIQUID            = 2097152
	SURF_CLIMABLE          = 4194304

	def __init__(self):
		self.flags = 0
		self.planes = []
		self.mesh = None
		self.bmin = Vec3(0.0, 0.0, 0.0)
		self.bmax = Vec3(0.0, 0.0, 0.0)

	def toBlender(self):
		self.mesh = Mesh()
		
		for p0 in self.planes:
			f = Face()
			f.data = []
			v = p0.normal * p0.distance
			c = Vec3(0.0, 0.0, 1.0)
			if p0.normal == c:
				c = Vec3(0.0, 1.0, 0.0)
			print(str(p0.normal) + " * " + str(p0.distance))
			axis_x = p0.normal.cross(c)
			axis_y = p0.normal.cross(axis_x)

			print(axis_x)
			print(axis_y)

			axis_x.normalise()
			axis_y.normalise()

			p = Vec3(v.data)
			p = p + axis_x * S2_SURF_SIZE_HALF
			p = p + axis_y * S2_SURF_SIZE_HALF
			vert = Vertex()
			vert.data = p.data[:]
			self.mesh.verts.append(vert)
			f.data.append(len(self.mesh.verts)-1)
			p = Vec3(v.data)
			p = p - axis_x * S2_SURF_SIZE_HALF
			p = p + axis_y * S2_SURF_SIZE_HALF
			vert = Vertex()
			vert.data = p.data[:]
			self.mesh.verts.append(vert)
			f.data.append(len(self.mesh.verts)-1)
			p = Vec3(v.data)
			p = p - axis_x * S2_SURF_SIZE_HALF
			p = p - axis_y * S2_SURF_SIZE_HALF
			vert = Vertex()
			vert.data = p.data[:]
			self.mesh.verts.append(vert)
			f.data.append(len(self.mesh.verts)-1)
			p = Vec3(v.data)
			p = p + axis_x * S2_SURF_SIZE_HALF
			p = p - axis_y * S2_SURF_SIZE_HALF
			vert = Vertex()
			vert.data = p.data[:]
			self.mesh.verts.append(vert)
			f.data.append(len(self.mesh.verts)-1)
			
			self.mesh.faces.append(f)
		self.mesh.numVerts = len(self.mesh.verts)
		self.mesh.numFaces = len(self.mesh.faces)

	#this function is only used to convert old-style surf plane defs to meshes
	def toMesh(self):
		self.mesh = Mesh()
		
		for p0 in self.planes:
			edges = []
			facePoints = []
			
			for p1 in [sp for sp in self.planes if sp is not p0]:
				#solve the intersection line, append it to edges
				
				l = line_t()
				l.a = p0.normal.cross(p1.normal)
				
				p2 = plane_t()
				if l.a.data[2] != 0.0:
					#find using z=0
					p2.normal.data[2] = 1.0
				else:
					#find using x=0 instead
					p2.normal.data[0] = 1.0
					
				x0 = p0.normal * p0.distance
				x1 = p1.normal * p1.distance
				x2 = p2.normal * p2.distance
				
				det = Vec3(1/max(1.0, p0.normal.data[0] * p1.normal.data[0] * p2.normal.data[0]),
						1/max(1.0, p0.normal.data[1] * p1.normal.data[1] * p2.normal.data[1]),
						1/max(1.0, p0.normal.data[2] * p1.normal.data[2] * p2.normal.data[2]))
						
				l.x0 = det * (x0.mult(p0.normal) * p1.normal.cross(p2.normal) + x1.mult(p1.normal) * p2.normal.cross(p0.normal) + x2.mult(p2.normal) * p0.normal.cross(p1.normal))
				
				l.x1 = l.x0 + l.a * 1000.0 #arbitrary
				l.x0 = l.x0 - l.a * 1000.0
				edges.append(l)

			for l0 in edges:
				for l1 in [e for e in edges if e is not l0]:
					#solve for the intersection point between the edges, if there is one.
					v = l0.intersection(l1)
					if v is None:
						continue
					
					#check if the point is already in verts, if not add it
					newVert = True
					for i, vert in enumerate(self.mesh.verts):
						if vert == v:
							facePoints.append(i)
							newVert = False
							break
					if newVert:
						vert = Vertex()
						vert.data = v.data[:]
						self.mesh.verts.append(vert)
						facePoints.append(len(self.mesh.verts)-1)
			
			#create the faces of the mesh
			face = Face()
			face.data = facePoints[:]
			self.mesh.faces.append(face)
		self.mesh.numFaces = len(self.mesh.faces)
		self.mesh.numVerts = len(self.mesh.verts)
