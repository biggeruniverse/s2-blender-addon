# (c) 2011 savagerebirth.com
# (c) 2023-2026 DRX Dev Team

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
                self.bmin = Vec3(1000000.0,1000000.0,1000000.0)
                self.bmax = Vec3(-1000000.0,-1000000.0,-1000000.0)

        def find_bone(self, name):
                #god damn this is disgusting...
                for i, bone in enumerate(self.bones):
                        if bone.name == name:
                                return i
                return -1

        def find_bone_parent_index(self, bone):
                """Return the integer parent index for a bone, regardless of
                whether bone.parent is already an int (fromBlender path) or a
                Bone object (loadFile path)."""
                p = bone.parent
                if p is None:
                        return -1
                if isinstance(p, int):
                        return p
                # It's a Bone object - find its index
                return p.idx

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
                                self.handleSingleLinksBlock(block)
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
                f.write(sr_io.int2str(0)) # <-- add later? (sprite count)
                f.write(sr_io.int2str(len(self.surfs)))
                f.write(sr_io.int2str(len(self.bones)))
                f.write(sr_io.float2str(self.bmin.data[0])); f.write(sr_io.float2str(self.bmin.data[1])); f.write(sr_io.float2str(self.bmin.data[2]));
                f.write(sr_io.float2str(self.bmax.data[0])); f.write(sr_io.float2str(self.bmax.data[1])); f.write(sr_io.float2str(self.bmax.data[2]));

                # Bone block
                boneblock = sr_io.FileBlock()
                boneblock.name = b'bone'
                for bone in self.bones:
                        boneblock.data += sr_io.int2str(self.find_bone_parent_index(bone))
                        name_bytes = bone.name[:Bone.NAME_LENGTH].encode('utf-8') if isinstance(bone.name, str) else bone.name[:Bone.NAME_LENGTH]
                        boneblock.data += name_bytes
                        boneblock.data += bytes(b'\0' * (Bone.NAME_LENGTH-len(name_bytes)))
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
                        # Mesh block
                        meshblock = sr_io.FileBlock()
                        meshblock.name = b'mesh'
                        meshblock.data += sr_io.int2str(idx)
                        name_bytes = mesh.name[:Mesh.NAME_LENGTH].encode('utf-8') if isinstance(mesh.name, str) else mesh.name[:Mesh.NAME_LENGTH]
                        tex_bytes  = mesh.texture[:Mesh.TEX_NAME_LENGTH].encode('utf-8') if isinstance(mesh.texture, str) else mesh.texture[:Mesh.TEX_NAME_LENGTH]
                        meshblock.data += name_bytes
                        meshblock.data += bytes(b'\0' * (Mesh.NAME_LENGTH-len(name_bytes)))
                        meshblock.data += tex_bytes
                        meshblock.data += bytes(b'\0' * (Mesh.TEX_NAME_LENGTH-len(tex_bytes)))
                        meshblock.data += sr_io.int2str(mesh.mode)
                        meshblock.data += sr_io.int2str(len(mesh.verts))
                        meshblock.data += sr_io.float2str(mesh.bmin.data[0]); meshblock.data += sr_io.float2str(mesh.bmin.data[1]); meshblock.data += sr_io.float2str(mesh.bmin.data[2]);
                        meshblock.data += sr_io.float2str(mesh.bmax.data[0]); meshblock.data += sr_io.float2str(mesh.bmax.data[1]); meshblock.data += sr_io.float2str(mesh.bmax.data[2]);
                        meshblock.data += sr_io.int2str(mesh.boneLink)
                        meshblock.write(f)

                        # Build up data blocks
                        vertblock = sr_io.FileBlock()
                        texcblock = sr_io.FileBlock()
                        colourblock = sr_io.FileBlock()
                        normalblock = sr_io.FileBlock()
                        vertblock.data += sr_io.int2str(idx)
                        texcblock.data += sr_io.int2str(idx)
                        colourblock.data += sr_io.int2str(idx)
                        normalblock.data += sr_io.int2str(idx)

                        for v in mesh.verts:
                                d = matrix.multiplyVector(yaw180, v)
                                vertblock.data += sr_io.float2str(d.data[0])
                                vertblock.data += sr_io.float2str(d.data[1])
                                vertblock.data += sr_io.float2str(d.data[2])
                                texcblock.data += sr_io.float2str(v.texcoord[0])
                                texcblock.data += sr_io.float2str(v.texcoord[1])
                                colourblock.data += struct.pack('B', int(v.color.data[0] * 255.0))
                                colourblock.data += struct.pack('B', int(v.color.data[1] * 255.0))
                                colourblock.data += struct.pack('B', int(v.color.data[2] * 255.0))
                                colourblock.data += struct.pack('B', int(v.color.data[3] * 255.0))
                                d = matrix.multiplyVector(yaw180, v.normal)
                                normalblock.data += sr_io.float2str(d.data[0])
                                normalblock.data += sr_io.float2str(d.data[1])
                                normalblock.data += sr_io.float2str(d.data[2])

                        # Vertex block
                        vertblock.name = b'vrts'
                        vertblock.write(f)

                        # Blended skinning block (only for skinned meshes)
                        if mesh.boneLink == -1:
                                print('skinning mesh', idx)
                                for bl in self.blendedLinks[idx]:
                                        linkblock = sr_io.FileBlock()
                                        linkblock.name = b'lnk1' # blended skinning always ?
                                        linkblock.data += sr_io.int2str(idx)
                                        linkblock.data += sr_io.int2str(len(mesh.verts))
                                        for bw in bl.links:
                                                linkblock.data += sr_io.int2str(bw.numWeights)
                                                for w in bw.weights:
                                                        linkblock.data += sr_io.float2str(w)
                                                for bi in bw.indexes:
                                                        linkblock.data += sr_io.int2str(bi)
                                        linkblock.write(f)

                        # Face block
                        faceblock = sr_io.FileBlock()
                        faceblock.name = b'face'
                        faceblock.data += sr_io.int2str(idx)
                        faceblock.data += sr_io.int2str(len(mesh.faces))
                        for face in mesh.faces:
                                faceblock.data += sr_io.int2str(face.data[0])
                                faceblock.data += sr_io.int2str(face.data[1])
                                faceblock.data += sr_io.int2str(face.data[2])
                        faceblock.write(f)

                        # Texture coord block
                        texcblock.name = b'texc'
                        texcblock.write(f)

                        # Vertex colour block
                        colourblock.name = b'colr'
                        colourblock.write(f)

                        # Normal block
                        normalblock.name = b'nrml'
                        normalblock.write(f)

                # Surface blocks
                for i, surf in enumerate(self.surfs):
                        #if surf.version > 3:
                        #        continue
                        surfblock = sr_io.FileBlock()
                        surfblock.name = b'surf'
                        surfblock.data += sr_io.int2str(i)
                        surfblock.data += sr_io.int2str(len(surf.planes))
                        for j in range(3):
                                surfblock.data += sr_io.float2str(surf.bmin.data[j])
                                surfblock.data += sr_io.float2str(surf.bmax.data[j])
                        for plane in surf.planes:
                                for j in range(3):
                                        surfblock.data += sr_io.float2str(plane.normal.data[j])
                                surfblock.data += sr_io.float2str(plane.distance)
                        surfblock.data += sr_io.int2str(surf.flags)
                        surfblock.write(f)

                f.close()
                print("Saved", filename)

        def handleHeaderBlock(self, block):
                if block.name != "head":
                        raise Exception("Not a valid model file!")
                self.version = sr_io.endianint(block.data[0:4])
                if self.version < 1 or self.version > 3:
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
                        offset += 4
                        bone.name = block.data[offset:offset+Bone.NAME_LENGTH].decode('utf-8').rstrip('\x00')
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
                                bone.invBase.pos.data[c] = sr_io.endianfloat(block.data[offset:offset+4])
                                offset += 4
                        offset += 4
                        for c in range(3):
                                for a in range(3):
                                        bone.base.axis[c].data[a] = sr_io.endianfloat(block.data[offset:offset+4])
                                        offset += 4
                                offset += 4
                        for c in range(3):
                                bone.base.pos.data[c] = sr_io.endianfloat(block.data[offset:offset+4])
                                offset += 4
                        offset += 4
                        #print(bone.name + ":\n"+str(bone.base))
                        #print(bone.invBase)
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
                for i in range(Mesh.TEX_NAME_LENGTH):
                        if block.data[offset + i] == 0:
                                break
                        mesh.texture = mesh.texture + chr(block.data[offset + i])
                offset += Mesh.TEX_NAME_LENGTH
                mesh.mode = sr_io.endianint(block.data[offset:offset+4])
                offset += 4
                mesh.numVerts = sr_io.endianint(block.data[offset:offset+4])
                offset += 4
                offset += 6 * 4 #skip bounding box
                mesh.boneLink = sr_io.endianint(block.data[offset:offset+4])
                self.meshes[meshIndex] = mesh
                # print(mesh.name, self.bones[mesh.boneLink].name)

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
                        n = Vec3(0, 0, 0)
                        for j in range(3):
                                n.data[j] = sr_io.endianfloat(block.data[offset:offset+4])
                                offset += 4
                        self.meshes[meshIndex].verts[i].normal.data = matrix.translateFromMatrix(yaw180, n).data

        def handleVertexBlock(self, block):
                offset = 4
                meshIndex = sr_io.endianint(block.data[0:4])
                for i in range(self.meshes[meshIndex].numVerts):
                        v = Vec3(0, 0, 0)
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
                        self.meshes[meshIndex].verts[i].texcoord = [u, v]

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

        def handleSingleLinksBlock(self, block):
            pass

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
                        surf.planes.append(p)
                surf.flags = sr_io.endianint(block.data[pos:pos+4])
                self.surfs[idx] = surf
