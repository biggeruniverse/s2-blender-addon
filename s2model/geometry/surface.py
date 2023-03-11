from .vectors import Vec3
from .mesh import Mesh;
from .face import Face;
from .vertex import Vertex;

class line_t:
	def __init__(self):
		self.a = Vec3(0.0, 0.0, 0.0)
		self.x0 = Vec3(0.0, 0.0, 0.0)
		self.x1 = None;
		
	def intersection(self, b):
		da = self.x1 - self.x0;
		db = b.x1 - b.x0;
		dc = b.x0 - self.x0;
		
		if dc * da.cross(db) != 0.0:
			return None;
		
		c = da.cross(db);
		s = (dc.cross(db) * c) / c.size2();
		
		if s >= 0.0 and s <= 1.0:
			return self.x0 + da * s;
			
		return None;

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

	#this function is only used to convert old-style surf plane defs to meshes
	def toMesh(self):
		self.mesh = Mesh();
		
		for p0 in self.planes:
			edges = [];
			facePoints = [];
			
			for p1 in [e for e in self.planes if p1 is not p0]:
				#solve the intersection line, append it to edges
				
				l = line_t();
				l.a = p0.normal.cross(p1.normal);
				
				p2 = plane_t();
				if l.a.data[2] != 0.0:
					#find using z=0
					p2.normal.data[2] = 1.0;
				else:
					#find using x=0 instead
					p2.normal.data[0] = 1.0;
					
				x0 = p0.normal * p0.distance;
				x1 = p1.normal * p1.distance;
				x2 = p2.normal * p2.distance;
				
				det = Vec3(1/(p0.normal.data[0] * p1.normal.data[0] * p2.normal.data[0]),
						1/(p0.normal.data[1] * p1.normal.data[1] * p2.normal.data[1]),
						1/(p0.normal.data[2] * p1.normal.data[2] * p2.normal.data[2]));
						
				l.x0 = det * (x0.mult(p0.normal) * p1.normal.cross(p2.normal) + x1.mult(p1.normal) * p2.normal.cross(p0.normal) + x2.mult(p2.normal) * p0.normal.cross(p1.normal));
				
				l.x1 = l.x0 + l.a * 5000.0; #arbitrary
				l.x0 = l.x0 - l.a * 5000.0;
				
				edges.append(l);

			for l0 in edges:
				for l1 in [e for e in edges if l1 is not l0]:
					#solve for the intersection point between the edges, if there is one.
					v = l0.intersection(l1);
					if v is None:
						continue;
					
					#check if the point is already in verts, if not add it
					newVert = True;
					for i, vert in enumerate(self.mesh.verts):
						if vert == v:
							facePoints.append(i);
							newVert = False;
					if newVert:
						print(v);
						self.mesh.verts.append(v);
						facePoints.append(len(self.mesh.verts)-1);
			
			#create the faces of the mesh
			i=1;
			j=1;
			face = Face();
			while i<len(facePoints):
				face.data[j] = facePoints[i];
				j=j+1;
				if j == 3:
					j=1;
					face.data[0] = facePoints[0];
					self.mesh.faces.append(face);
					face = Face();
					continue;
				i=i+1;
				
