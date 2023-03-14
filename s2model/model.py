# (c) 2011 savagerebirth.com
# (c) 2023 DRX Dev Team

import os
import struct
from .geometry.vectors import Vec3
from .geometry.vertex import Vertex
from .geometry.face import Face
from .geometry.mesh import Mesh
from .geometry.surface import *
from s2model import sr_io
from .animation.bone import Bone
from .geometry.blendedlinks import *
import s2model.geometry.matrix as matrix

yaw180 = matrix.matrix43_t()
yaw180.axis = matrix.rotateMatrix(0, 0, 180)
class S2Model:
        def __init__(self):
                self.version = 3
                self.blocks = []
                self.bones = []
                self.meshes = []
                self.blendedLinks = []
                self.singleLinks = []
                self.surfs = []
                self.filepath = "."

        def find_bone(self, name):
                #god damn this is disgusting...
                for i, bone in enumerate(self.bones):
                        if bone.name == name:
                                return i
                return -1

        def loadFile(self, filename):
                self.filepath = filename
                size = os.path.getsize(filename)
                file = open(filename, "rb")
                filehead = file.read(4)
                if filehead != b'SMDL':
                        raise Exception("not a valid S2 model file! ("+str(filehead)+")")
		# chunk the file out into blocks
                while file.tell()+8 < size:
                        block = sr_io.FileBlock()
                        block.read(file, size)
                        self.blocks.append(block)
		# done with this
                file.close()
		
		#the header block comes first, but the order of 
		#other blocks isn't important to the file
                self.handleHeaderBlock(self.blocks[0])
		
		# make sure to handle bones first, so that we have something to link verts to
                self.handleBoneBlock(self.blocks[1])
		
		#TODO: Blender-specific stuff to put bones in the scene

                for block in self.blocks[2:]:
                        if block.name == "vrts":
                                self.handleVertexBlock(block)
                        elif block.name == "face":
                                self.handleFaceBlock(block)
                        elif block.name == "nrml":
                                self.handleNormalBlock(block)
                        elif block.name == "mesh":
                                self.handleMeshBlock(block)
                        elif block.name == "texc":
                                self.handleTextureCoordBlock(block)
                        elif block.name == "colr":
                                self.handleColorBlock(block)
                        elif block.name == "lnk1":
                                self.handleBlendedLinksBlock(block)
                        elif block.name == "lnk2":
                                pass #we don't support this yet
                        elif block.name == "surf":
                                self.handleSurfBlock(block)
                        else:
                                raise Exception("Invalid block name "+block.name)

        def saveFile(self, filename):
                f = open(filename, 'wb')
                f.write(b'SMDL')
                
                f.write(b'head')
                f.write(sr_io.int2str(44)) # block length
                f.write(sr_io.int2str(3))
                f.write(sr_io.int2str(len(self.meshes)))
                f.write(sr_io.int2str(0)) # <-- add later?
                f.write(sr_io.int2str(len(self.surfs)))
                f.write(sr_io.int2str(len(self.bones)))
                f.write(b'\0' * 24) # bmin, bmax, fix later

                boneblock = sr_io.FileBlock()
                boneblock.name = b'bone'
                for bone in self.bones:
                        boneblock.data += sr_io.int2str(bone.parent)
                        for i in range(Bone.NAME_LENGTH):
                                name = bone.name.encode()
                                if i < len(name):
                                        boneblock.data += name[i].to_bytes(1, 'big')
                                else:
                                        boneblock.data += b'\0'
                        for c in range(3):
                                for a in range(3):
                                        boneblock.data += sr_io.float2str(bone.invBase.axis[c].data[a])
                                boneblock.data += sr_io.float2str(0.0)
                        for c in range(3):
                                boneblock.data += sr_io.float2str(bone.invBase.pos.data[c])
                        boneblock.data += sr_io.float2str(1.0)
                        for c in range(3):
                                for a in range(3):
                                        boneblock.data += sr_io.float2str(bone.base.axis[c].data[a])
                                boneblock.data += sr_io.float2str(0.0)
                        for c in range(3):
                                boneblock.data += sr_io.float2str(bone.base.pos.data[c])
                        boneblock.data += sr_io.float2str(1.0)
                boneblock.write(f)

                for idx, mesh in enumerate(self.meshes):
                        meshblock = sr_io.FileBlock()
                        meshblock.name = b'mesh'
                        meshblock.data += sr_io.int2str(idx)
                        name = mesh.name.encode()
                        tex = mesh.texture.encode()
                        for i in range(Mesh.NAME_LENGTH):
                                if i < len(mesh.name):
                                        meshblock.data += name[i].to_bytes(1, 'big')
                                else:
                                        meshblock.data += b'\0'
                        for i in range(64):
                                if i < len(mesh.texture):
                                        meshblock.data += tex[i].to_bytes(1, 'big')
                                else:
                                        meshblock.data += b'\0'
                        meshblock.data += sr_io.int2str(1) # mode, fix later
                        meshblock.data += sr_io.int2str(len(mesh.verts))
                        meshblock.data += b'\0' * 24 # bmin, bmax, fix later
                        meshblock.data += sr_io.int2str(mesh.boneLink)
                        meshblock.write(f)

                        # vertex data
                        vertblock = sr_io.FileBlock()
                        vertblock.name = b'vrts'
                        vertblock.data += sr_io.int2str(idx)
                        for v in mesh.verts:
                                vertblock.data += sr_io.float2str(v.data[0])
                                vertblock.data += sr_io.float2str(v.data[1])
                                vertblock.data += sr_io.float2str(v.data[2])
                        vertblock.write(f)

                        if(mesh.boneLink == -1):
                                print('skinning')
                                for bl in self.blendedLinks[idx]:
                                        # skinning data
                                        linkblock = sr_io.FileBlock()
                                        linkblock.name = b'lnk1' # blended skinning always ?
                                        linkblock.data += sr_io.int2str(idx)
                                        linkblock.data += sr_io.int2str(len(mesh.verts))
                                        for bw in bl.links:
                                                linkblock.data += sr_io.int2str(bw.numWeights)
                                                for w in bw.weights:
                                                        linkblock.data += sr_io.float2str(w)
                                                for i in bw.indexes:
                                                        linkblock.data += sr_io.int2str(i)
                                        linkblock.write(f)
                                print('end skinning')

                        # face data
                        faceblock = sr_io.FileBlock()
                        faceblock.name = b'face'
                        faceblock.data += sr_io.int2str(idx)
                        faceblock.data += sr_io.int2str(len(mesh.faces))
                        for face in mesh.faces:
                                faceblock.data += sr_io.int2str(face.data[0])
                                faceblock.data += sr_io.int2str(face.data[1])
                                faceblock.data += sr_io.int2str(face.data[2])
                        faceblock.write(f)

                        # texture coords
                        texcblock = sr_io.FileBlock()
                        texcblock.name = b'texc'
                        texcblock.data += sr_io.int2str(idx)
                        for v in mesh.verts:
                                texcblock.data += sr_io.float2str(v.texcoord[0])
                                texcblock.data += sr_io.float2str(v.texcoord[1])
                        texcblock.write(f)

                        # vertex colours
                        colourblock = sr_io.FileBlock()
                        colourblock.name = b'colr'
                        colourblock.data += sr_io.int2str(idx)
                        for v in mesh.verts:
                                for i in range(4):
                                        colourblock.data += sr_io.int2str(int(v.color.data[i] * 255.0))[0].to_bytes(1, 'big')
                        colourblock.write(f)

                        # normals
                        normalblock = sr_io.FileBlock()
                        normalblock.name = b'nrml'
                        normalblock.data += sr_io.int2str(idx)
                        for v in mesh.verts:
                                normalblock.data += sr_io.float2str(v.normal.data[0])
                                normalblock.data += sr_io.float2str(v.normal.data[1])
                                normalblock.data += sr_io.float2str(v.normal.data[2])
                        normalblock.write(f)

                for i in range(len(self.surfs)):
                        surf = self.surfs[i]
                        #if surf.version > 3:
                        #        continue
                        surfblock = sr_io.FileBlock()
                        surfblock.name = b'surf'
                        surfblock.data += sr_io.int2str(i) # surf id
                        surfblock.data += sr_io.int2str(len(surf.planes))
                        for j in range(3):
                                surfblock.data += sr_io.float2str(surf.bmin.data[j])
                                surfblock.data += sr_io.float2str(surf.bmax.data[j])
                        
                        for plane in surf.planes:
                                for j in range(3):
                                        surfblock.data += sr_io.float2str(plane.normal.data[j])
                                surfblock.data += sr_io.float2str(plane.distance)
                        surfblock.data += sr_io.int2str(surf.flags) # flags
                        surfblock.write(f)

                f.close()
		
        def handleHeaderBlock(self, block):
                if block.name != "head":
                        raise Exception("Not a valid model file!")
                self.version = sr_io.endianint(block.data[0:4])
                if self.version<1 or self.version > 3:
                        raise Exception("Bad version "+str(self.version))

                numMeshes = sr_io.endianint(block.data[4:8])
                self.meshes = [None] * numMeshes
                #sprites do we care?
                numSurfs = sr_io.endianint(block.data[12:16])
                self.surfs = [None] * numSurfs
                numBones = sr_io.endianint(block.data[16:20])
                self.bones = []
                for i in range(numBones):
                        self.bones.append(Bone())
                for i in range(numMeshes):
                        self.blendedLinks.append([])

        def handleBoneBlock(self, block):
                offset = 0
		
                for i in range(len(self.bones)):
                        bone = self.bones[i]
                        bone.idx = i
                        parent = sr_io.endianint(block.data[offset:offset+4])
                        offset+=4
                        bone.name = block.data[offset:offset+Bone.NAME_LENGTH].decode('utf-8')
                        offset += Bone.NAME_LENGTH
                        #print str(parent) + "bone "+str(i)+" "+bone.name+" "+str(parent)
                        if parent >= 0 and parent < len(self.bones):
                                bone.parent = self.bones[parent]
                                self.bones[parent].add(bone)
			#self.bones.append(bone)
                                
                        for c in range(3):
                                for a in range(3):
                                        bone.invBase.axis[c].data[a] = sr_io.endianfloat(block.data[offset:offset+4])
                                        offset += 4
                                offset += 4
                        for c in range(3):
                                bone.invBase.pos.data[c] = sr_io.endianfloat(block.data[offset:offset+4])# * 0.4
                                offset += 4
                        offset += 4
                        
                        for c in range(3):
                                for a in range(3):
                                        bone.base.axis[c].data[a] = sr_io.endianfloat(block.data[offset:offset+4])
                                        offset += 4
                                offset += 4
                        for c in range(3):
                                bone.base.pos.data[c] = sr_io.endianfloat(block.data[offset:offset+4])# * 0.4
                                offset += 4
                        offset += 4

                        # 'fix' the bone matrix
                        #bone.base = matrix.multiplyMatrix(bone.base, yaw180)
                        #bone.invBase = matrix.multiplyMatrix(bone.invBase, yaw180)

                # calculate the local base of each bone
                for i in range(len(self.bones)):
                        bone = self.bones[i]
                        if bone.parent is not None:
                                bone.localBase = matrix.multiplyMatrix(bone.parent.invBase, bone.base)
                                #bone.localBase = matrix.multiplyMatrix(bone.localBase, yaw180)
                        else:
                                bone.localBase.copyFrom(bone.base)
                                #bone.localBase = matrix.multiplyMatrix(bone.localBase, yaw180)
	
        def handleMeshBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                mesh = Mesh()
                mesh.name = ""
                mesh.texture = ""
                for i in range(Mesh.NAME_LENGTH):
                        if block.data[offset + i] == 0:
                                break
                        mesh.name = mesh.name + chr(block.data[offset + i])
                offset += Mesh.NAME_LENGTH
                for i in range(64):
                        if block.data[offset + i] == 0:
                                break
                        mesh.texture = mesh.texture + chr(block.data[offset + i])
                offset += 64
                offset += 4 #skip mode
                mesh.numVerts = sr_io.endianint(block.data[offset:offset+4])
                offset += 4
                offset += 6 * 4 #skip bounding box
                mesh.boneLink = sr_io.endianint(block.data[offset:offset+4])
                self.meshes[meshIndex] = mesh
	
        def handleFaceBlock(self, block):
                offset = 8
                meshIndex = sr_io.endianint(block.data[0:4])
                self.meshes[meshIndex].numFaces = sr_io.endianint(block.data[4:8])
                for i in range(self.meshes[meshIndex].numFaces):
                        face = Face()
                        for j in range(3):
                                face.data[j] = sr_io.endianint(block.data[offset:offset+4])
                                offset += 4
                        self.meshes[meshIndex].faces.append(face)

        def handleNormalBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                for i in range(self.meshes[meshIndex].numVerts):
                        for j in range(3):
                                self.meshes[meshIndex].verts[i].normal.data[j] = sr_io.endianfloat(block.data[offset:offset+4])
                                offset += 4

        def handleVertexBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                for i in range(self.meshes[meshIndex].numVerts):
                        v = Vec3(0,0,0)
                        for j in range(3):
                                v.data[j] = sr_io.endianfloat(block.data[offset:offset+4])
                                offset += 4
                        v = matrix.translateFromMatrix(yaw180, v)
                        vert = Vertex()#v.data[0], v.data[1], v.data[2])
                        vert.data = v.data
                        self.meshes[meshIndex].verts.append(vert)

        def handleTextureCoordBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                for i in range(self.meshes[meshIndex].numVerts):
                        u = sr_io.endianfloat(block.data[offset:offset+4])
                        offset += 4
                        v = sr_io.endianfloat(block.data[offset:offset+4])
                        offset += 4
                        self.meshes[meshIndex].verts[i].texcoord = [u,v]

        # vertex colors
        def handleColorBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                for i in range(self.meshes[meshIndex].numVerts):
                        self.meshes[meshIndex].verts[i].color.data = [ struct.unpack_from("B", block.data, offset+j)[0]/255.0 for j in range(4) ]
                        offset += 4

        def handleBlendedLinksBlock(self, block):
                meshIndex = sr_io.endianint(block.data[0:4])
                numVerts = sr_io.endianint(block.data[4:8])
                pos = 8

                bl = blendedLinkGroup()
                bl.mesh = meshIndex
                for i in range(numVerts):
                        bw = blendedWeights()
                        bw.numWeights = sr_io.endianint(block.data[pos:pos+4])
                        pos += 4
                        for w in range(bw.numWeights):
                                bw.weights.append(sr_io.endianfloat(block.data[pos:pos+4]))
                                pos += 4
                        for w in range(bw.numWeights):
                                bw.indexes.append(sr_io.endianint(block.data[pos:pos+4]))
                                pos += 4
                        bl.links.append(bw)
                self.blendedLinks[meshIndex].append(bl)

        def handleSurfBlock(self, block):
                #converting surfs from old s2 models is a huge pain...
                surf = surface_t()
                idx = sr_io.endianint(block.data[0:4])
                numPlanes = sr_io.endianint(block.data[4:8])
                pos = 8

                for i in range(3):
                    surf.bmin.data[i] = sr_io.endianfloat(block.data[pos:pos+4])
                    pos += 4
                    surf.bmax.data[i] = sr_io.endianfloat(block.data[pos:pos+4])
                    pos += 4
                
                for i in range(numPlanes):
                    p = plane_t()
                    for j in range(3):
                        p.normal.data[j] = sr_io.endianfloat(block.data[pos:pos+4])
                        pos += 4
                    p.distance = sr_io.endianfloat(block.data[pos:pos+4])
                    pos += 4
                surf.flags = sr_io.endianint(block.data[pos:pos+4])

                self.surfs[idx] = surf
