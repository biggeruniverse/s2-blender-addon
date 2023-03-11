import os,sys,mathutils,math

import bpy
from bpy_extras.image_utils import load_image
from bpy_extras import node_shader_utils

def meshToBlender(mesh, model, skel):
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

    if mesh.boneLink > -1:
        bone = skel.bones[mesh.boneLink]
        blmesh.vertex_groups.add(name=bone.name)
        for i, v in enumerate(mesh.verts):
            blmesh.vertex_groups[0].add(i, 1.0)
    elif model.blendedLinks or model.singleLinks:
        for bone in skel.bones:
            blmesh.vertex_groups.add(name=bone.name)
        #TODO: blended links stuff

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
    if model.bones:
        jointls = []
        bonels = [None] * len(model.bones)
        
        for bone in model.bones:
            if bone.parent == None:
                bn = skel.edit_bones.new(bone.name)
                bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
                bn.tail = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2]+1)
                bonels[bone.idx] = bn

                for child in bone.children:
                    jointls.append((child, bn, bone))

        for joint in jointls:
            bone = joint[0]
            bn = skel.edit_bones.new(bone.name)
            bn.parent = joint[1]
            bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
            pos = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2]+1)
            if bone.children:
                pos = (bone.children[0].base.pos.data[0],bone.children[0].base.pos.data[1],bone.children[0].base.pos.data[2])
            bn.tail = pos
            bonels[bone.idx] = bn
            for child in bone.children:
                jointls.append((child, bn, bone))

    skel.transform(mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z'))            
        
    
    #create mesh objects
    for m in model.meshes:
        mesh = bpy.data.objects.new(m.name, meshToBlender(m, model, skel))
        mesh.parent = parent
        bpy.context.collection.objects.link(mesh)

    for i, surf in enumerate(model.surfs):
        if surf.mesh is None:
            #TODO: the surface_t.toMesh() function doesn't actually work.
            #surf.toMesh()
            continue
        blmesh = meshToBlender(surf.mesh, model)
        bpy.data.objects.new("_surf%03d" % i, blmesh)
        blmesh.parent = parent
        bpy.context.collection.objects.link(blmesh)

def addMesh(model, item, bones):
    mesh = Mesh()
    mesh.name = item.name
    #mesh.texture = item.texture
    for face in item.data.polygons:
        verts_in_face = face.vertices[:]
        print("face index ", face.index)
        print("normal ", face.normal)
        for vert in verts_in_face:
            print("vertex coords ", item.data.vertices[vert].co)

def fromBlender(useSelection = False):
    model = S2Model()

    root_bone = Bone()
    root_bone.base = matrix.matrix43_t()
    root_bone.invBase = matrix.matrix43_t()
    root_bone.idx = 0
    root_bone.name = 'Scene Root'
    root_bone.parent = -1
    model.bones.append(root_bone)

    for item in bpy.data.objects:
        if item.type == 'MESH' :
            addMesh(model, item, None)

    return model
