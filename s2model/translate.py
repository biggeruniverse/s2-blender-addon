import os,sys,mathutils,math

import bpy
from bpy_extras.image_utils import load_image
from bpy_extras import node_shader_utils

from s2model import model
from .geometry.mesh import Mesh
from .geometry.surface import *
from .animation.bone import Bone
from .geometry.blendedlinks import *
import s2model.geometry.matrix as matrix


def meshToBlender(mesh, model, midx, skel):
    mesh_uvs = []
    blmesh = bpy.data.meshes.new(name=mesh.name)

    blmesh.vertices.add(mesh.numVerts)

    blmesh.vertices.foreach_set("co", [a for v in mesh.verts for a in (v.data[0], v.data[1], v.data[2])])

    loops = []
    faces_loop_start = []
    faces_loop_total = []
    lidx = 0
    for f in mesh.faces:
        mesh_uvs.extend([(mesh.verts[i].texcoord[0], 1.0-mesh.verts[i].texcoord[1]) for i in f.data])
        loops.extend(f.data)
        faces_loop_start.append(lidx)
        faces_loop_total.append(3)
        lidx += 3

    blmesh.loops.add(len(loops))
    blmesh.polygons.add(len(mesh.faces))

    blmesh.loops.foreach_set("vertex_index", loops)
    blmesh.polygons.foreach_set("loop_start", faces_loop_start)
    blmesh.polygons.foreach_set("loop_total", faces_loop_total)

    uv_layer = blmesh.uv_layers.new()
    for i, uv in enumerate(uv_layer.data):
        uv.uv = mesh_uvs[i]

    blmesh.update()
    blmesh.validate()

    #encoding = sys.getfilesystemencoding()
    encoded_texture = mesh.texture.replace('.tga', '.png')
    name = bpy.path.display_name_from_filepath(mesh.texture)
    image = load_image(encoded_texture, os.path.dirname(model.filepath), recursive=True, place_holder=True)

    if image:
        material = bpy.data.materials.new(name=name)

        mtex = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        mtex.base_color_texture.image = image
        mtex.base_color_texture.texcoords = 'UV'
        #mtex.base_color_texture.use_alpha = True

        blmesh.materials.append(material)
        #for face in blmesh.uv_textures[0].data:
        #    face.image = image

    return blmesh

def toBlender(model):
    #create the parent object
    for ob in bpy.context.selected_objects:
        ob.select_set(False)

    parent = bpy.data.objects.new(bpy.path.display_name_from_filepath(model.filepath), None)
    bpy.context.collection.objects.link(parent)
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)

    bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', scale=(1, 1, 1))

    skel = bpy.data.armatures[-1]

    #create the bones if any
    bone_map = {}
    bcount = 1
    if model.bones:
        jointls = []
        bonels = [None] * len(model.bones)
        
        for bone in model.bones:
            if bone.parent == None:
                bone_map[bone.idx] = 0
                bn = skel.edit_bones[0]
                bn.name = bone.name
                bn.matrix = [[bone.base.axis[0].data[0], bone.base.axis[0].data[1], bone.base.axis[0].data[2], 0.0],
                                                [bone.base.axis[1].data[0], bone.base.axis[1].data[1], bone.base.axis[1].data[2], 0.0],
                                                [bone.base.axis[2].data[0], bone.base.axis[2].data[1], bone.base.axis[2].data[2], 0.0],
                                                [bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2], 1.0]]
                bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
                bn.tail = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2]+1)
                bonels[bone.idx] = bn

                for child in bone.children:
                    jointls.append((child, bn, bone))

        for joint in jointls:
            bone = joint[0]
            bn = skel.edit_bones.new(bone.name)
            bone_map[bone.idx] = bcount
            print("child bone "+bone.name+" "+str(bcount))
            bcount += 1
            bn.parent = joint[1]
            bn.matrix = [[bone.base.axis[0].data[0], bone.base.axis[0].data[1], bone.base.axis[0].data[2], 0.0],
                            [bone.base.axis[1].data[0], bone.base.axis[1].data[1], bone.base.axis[1].data[2], 0.0],
                            [bone.base.axis[2].data[0], bone.base.axis[2].data[1], bone.base.axis[2].data[2], 0.0],
                            [bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2], 1.0]]
            bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
            pos = (bone.base.pos.data[0], bone.base.pos.data[1]-2, bone.base.pos.data[2])
            if bone.children:
                pos = (bone.children[0].base.pos.data[0],bone.children[0].base.pos.data[1],bone.children[0].base.pos.data[2])
            bn.tail = pos
            bonels[bone.idx] = bn
            for child in bone.children:
                jointls.append((child, bn, bone))

    skel.transform(mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z'))            
    
    print("skel set: "+str([bone.name for bone in skel.edit_bones]))
    #create mesh objects
    for idx, m in enumerate(model.meshes):
        mesh = bpy.data.objects.new(m.name, meshToBlender(m, model, idx, skel))
        mesh.parent = parent

        #link bones
        if m.boneLink > -1:
            bone = skel.edit_bones[m.boneLink]
            mesh.vertex_groups.new(name=bone.name)
            for i, v in enumerate(m.verts):
                mesh.vertex_groups[0].add([i], 1.0, 'ADD')
        elif model.blendedLinks:
            #build a set of unique bones referenced by this mesh
            bone_set = set()
            for grp in model.blendedLinks[idx]:
                for bw in grp.links:
                    for b in bw.indexes:
                        bone_set.add(b)

            bone_set = list(bone_set) #the ol' switcharoo!
            print("bone set: "+str(bone_set))
            for bone in bone_set:
                bname = skel.edit_bones[bone_map[bone]].name
                print("group named "+bname)
                mesh.vertex_groups.new(name=bname)
            #blended links stuff
            for grp in model.blendedLinks[idx]:
                for i,bw in enumerate(grp.links):
                    for b in range(bw.numWeights):
                        bwi = bone_set.index(bw.indexes[b])
                        mesh.vertex_groups[bwi].add([i], bw.weights[b], 'ADD')

        bpy.context.collection.objects.link(mesh)

    for i, surf in enumerate(model.surfs):
        if surf.mesh is None:
            #FIXME: the surface_t.toMesh() function doesn't actually work.
            surf.toMesh()
        blmesh = meshToBlender(surf.mesh, model)
        bpy.data.objects.new("_surf%03d" % i, blmesh)
        blmesh.parent = parent
        bpy.context.collection.objects.link(blmesh)

def addMesh(mdl, item, i, bones):
    print("Adding mesh "+str(i))
    mesh = Mesh()
    mesh.name = item.name
    #mesh.texture = item.texture
    for i,vert in enumerate(item.data.vertices):
        v = Vertex()
        v.data = [item.data.vertices[i].co[0], item.data.vertices[i].co[2], -item.data.vertices[1].co[1]]
        v.normal.data = [item.data.vertices[i].normal[0], item.data.vertices[i].normal[2], -item.data.vertices[1].normal[1]]
        mesh.verts.append(v)
    mesh.numVerts = len(mesh.verts)

    for face in item.data.polygons:
        verts_in_face = face.vertices[:]
        f = Face()
        for vert in verts_in_face:
            f.data.append(vert)
        mesh.faces.append(f)
        mesh.numFaces = len(mesh.faces)

    #FIXME: if we've only got one bone, it's a rigid mesh, not blended
    mesh.blend = True
    blList = blendedLinkGroup()
    blList.mesh = i

    mdl.meshes.append(mesh)
    mdl.blendedLinks[-1].append(blList)

def addSurf(mdl, item):
    surf = surface_t()
    #TODO: get the surf mesh and turn it into a set of planes
    mdl.surfs.append(surf)

def fromBlender(useSelection = False):
    mdl = model.S2Model()

    root_bone = Bone()
    root_bone.base = matrix.matrix43_t()
    root_bone.invBase = matrix.matrix43_t()
    root_bone.idx = 0
    root_bone.name = 'Scene Root'
    root_bone.parent = -1
    mdl.bones.append(root_bone)

    #capture the skeleton
    skel = bpy.data.armatures[-1]
    for bone in skel.bones[1:]:
        bn = Bone()
        bn.base = matrix.fromBlenderMatrix([list(i) for i in bone.matrix]+[[bone.head[0],bone.head[1],bone.head[2],1.0]])
        bn.invBase = matrix.matrix43_t()
        bn.idx = len(mdl.bones)
        bn.name = bone.name
        bn.parent = skel.bones.find(bone.parent.name)
        mdl.bones.append(bn)

    mcount = 0
    for item in bpy.data.objects:
        if item.type == 'MESH':
            if item.name.startswith("_surf"):
                addSurf(mdl, item)
            else:
                mdl.blendedLinks.append([])
                addMesh(mdl, item, mcount, None)
                mcount += 1

    return mdl
