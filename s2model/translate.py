# (c) 2023 DRX Dev Team

import os, sys, mathutils, math

import bpy
from bpy_extras.image_utils import load_image
from bpy_extras import node_shader_utils

from s2model import model
from .geometry.mesh import Mesh
from .geometry.surface import *
from .animation.bone import Bone
from .geometry.blendedlinks import *
from .geometry.vertex import Vertex
from .geometry.face import Face
import s2model.geometry.matrix as matrix


def meshToBlender(mesh, mdl, midx, skel):
    mesh_uvs = []
    blmesh = bpy.data.meshes.new(name=mesh.name)

    blmesh.vertices.add(mesh.numVerts)
    blmesh.vertices.foreach_set("co",     [a for v in mesh.verts for a in (v.data[0], v.data[1], v.data[2])])
    blmesh.vertices.foreach_set("normal", [a for v in mesh.verts for a in (v.normal.data[0], v.normal.data[1], v.normal.data[2])])

    loops = []
    faces_loop_start = []
    faces_loop_total = []
    lidx = 0
    for f in mesh.faces:
        mesh_uvs.extend([(mesh.verts[i].texcoord[0], 1.0 - mesh.verts[i].texcoord[1]) for i in f.data])
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

    encoded_texture = mesh.texture.replace('.tga', '.png')
    name = bpy.path.display_name_from_filepath(mesh.texture)
    image = load_image(encoded_texture, os.path.dirname(mdl.filepath), recursive=True, place_holder=True)

    if image:
        material = bpy.data.materials.new(name=name)
        mtex = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        mtex.base_color_texture.image = image
        mtex.base_color_texture.texcoords = 'UV'
        blmesh.materials.append(material)

    blmesh.transform(mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z'))
    return blmesh


def surfMeshToBlender(surf_mesh, surf_name):
    """Build a Blender mesh from a surface_t mesh (may contain quads, no UVs needed)."""
    count = bpy.data.meshes
    blmesh = bpy.data.meshes.new(name=surf_name)
    blmesh.vertices.add(surf_mesh.numVerts)
    blmesh.vertices.foreach_set("co", [a for v in surf_mesh.verts for a in (v.data[0], v.data[1], v.data[2])])

    loops = []
    faces_loop_start = []
    faces_loop_total = []
    lidx = 0
    for f in surf_mesh.faces:
        n = len(f.data)
        loops.extend(f.data)
        faces_loop_start.append(lidx)
        faces_loop_total.append(n)
        lidx += n

    blmesh.loops.add(len(loops))
    blmesh.polygons.add(surf_mesh.numFaces)
    blmesh.loops.foreach_set("vertex_index", loops)
    blmesh.polygons.foreach_set("loop_start", faces_loop_start)
    blmesh.polygons.foreach_set("loop_total", faces_loop_total)
    blmesh.update()
    blmesh.validate()
    return blmesh


def toBlender(mdl):
    #create the parent object
    for ob in bpy.context.selected_objects:
        ob.select_set(False)

    parent = bpy.data.objects.new(bpy.path.display_name_from_filepath(mdl.filepath), None)
    bpy.context.collection.objects.link(parent)
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)

    bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', scale=(1, 1, 1))
    skel = bpy.data.armatures[-1]

    bone_map = {}
    bcount = 1
    if mdl.bones:
        jointls = []
        bonels = [None] * len(mdl.bones)

        for bone in mdl.bones:
            if bone.parent is None:
                bone_map[bone.idx] = 0
                bn = skel.edit_bones[0]
                bn.name = bone.name
                bn.matrix = [
                    [bone.base.axis[0].data[0], bone.base.axis[0].data[1], bone.base.axis[0].data[2], 0.0],
                    [bone.base.axis[1].data[0], bone.base.axis[1].data[1], bone.base.axis[1].data[2], 0.0],
                    [bone.base.axis[2].data[0], bone.base.axis[2].data[1], bone.base.axis[2].data[2], 0.0],
                    [bone.base.pos.data[0],     bone.base.pos.data[1],     bone.base.pos.data[2],     1.0],
                ]
                bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
                bn.tail = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2] + 1)
                bonels[bone.idx] = bn
                for child in bone.children:
                    jointls.append((child, bn, bone))

        for joint in jointls:
            bone = joint[0]
            bn = skel.edit_bones.new(bone.name)
            bone_map[bone.idx] = bcount
            bcount += 1
            bn.parent = joint[1]
            bn.matrix = [
                [bone.base.axis[0].data[0], bone.base.axis[0].data[1], bone.base.axis[0].data[2], 0.0],
                [bone.base.axis[1].data[0], bone.base.axis[1].data[1], bone.base.axis[1].data[2], 0.0],
                [bone.base.axis[2].data[0], bone.base.axis[2].data[1], bone.base.axis[2].data[2], 0.0],
                [bone.base.pos.data[0],     bone.base.pos.data[1],     bone.base.pos.data[2],     1.0],
            ]
            bn.head = (bone.base.pos.data[0], bone.base.pos.data[1], bone.base.pos.data[2])
            pos = (bone.base.pos.data[0], bone.base.pos.data[1] - 2, bone.base.pos.data[2])
            if bone.children:
                pos = (bone.children[0].base.pos.data[0],
                       bone.children[0].base.pos.data[1],
                       bone.children[0].base.pos.data[2])
            bn.tail = pos
            bonels[bone.idx] = bn
            for child in bone.children:
                jointls.append((child, bn, bone))

    # Create mesh objects
    for idx, m in enumerate(mdl.meshes):
        mesh_obj = bpy.data.objects.new(m.name, meshToBlender(m, mdl, idx, skel))
        mesh_obj.parent = parent

        if m.boneLink > -1:
            if m.boneLink < len(skel.edit_bones):
                bone = skel.edit_bones[m.boneLink]
                mesh_obj.vertex_groups.new(name=bone.name)
                for i in range(len(m.verts)):
                    mesh_obj.vertex_groups[0].add([i], 1.0, 'ADD')
        elif mdl.blendedLinks:
            bone_set = set()
            for grp in mdl.blendedLinks[idx]:
                for bw in grp.links:
                    for b in bw.indexes:
                        bone_set.add(b)
            bone_set = list(bone_set)
            for b in bone_set:
                bname = skel.edit_bones[bone_map[b]].name
                mesh_obj.vertex_groups.new(name=bname)
            for grp in mdl.blendedLinks[idx]:
                for i, bw in enumerate(grp.links):
                    for b in range(bw.numWeights):
                        bwi = bone_set.index(bw.indexes[b])
                        mesh_obj.vertex_groups[bwi].add([i], bw.weights[b], 'ADD')

        bpy.context.collection.objects.link(mesh_obj)

    # Create _surf objects so they survive the import→export round-trip.
    # surf.toBlender() converts the plane list into a small mesh we can put in the scene.
    for i, surf in enumerate(mdl.surfs):
        if surf.mesh is None:
            surf.toBlender()
        name = "_surf%03d" % i
        blmesh = surfMeshToBlender(surf.mesh, name)
        surf_obj = bpy.data.objects.new(name, blmesh)
        surf_obj.hide_render = True
        bpy.context.collection.objects.link(surf_obj)

    bpy.ops.object.editmode_toggle()


def addMesh(mdl, item, midx, bones):
    print("Adding mesh " + str(midx))
    mesh = Mesh()
    mesh.name = item.name
    blmesh = item.data

    for slot in item.material_slots:
        if slot.material and slot.material.use_nodes:
            for n in slot.material.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    mesh.texture = bpy.path.display_name_from_filepath(n.image.filepath) + ".tga"
                    break

    # Triangulate a copy so we always work with triangles
    import bmesh as bm_module
    bm = bm_module.new()
    bm.from_mesh(blmesh)
    bm_module.ops.triangulate(bm, faces=bm.faces)
    tri_mesh = bpy.data.meshes.new("_tmp_tri")
    bm.to_mesh(tri_mesh)
    bm.free()

    tri_mesh.calc_loop_triangles()

    # UVs are per-loop in Blender; build a per-vertex UV by using the last loop
    # that references each vertex (consistent with what the importer writes).
    uv_layer = tri_mesh.uv_layers[0] if tri_mesh.uv_layers else None
    uv_map = {}  # vertex_index -> (u, v)
    if uv_layer:
        for lt in tri_mesh.loop_triangles:
            for vi, li in zip(lt.vertices, lt.loops):
                uv = uv_layer.data[li].uv
                uv_map[vi] = (uv[0], 1.0 - uv[1])

    # Build vertex list
    for i, vert in enumerate(tri_mesh.vertices):
        v = Vertex()
        v.data = [vert.co[0], vert.co[1], vert.co[2]]
        v.normal.data = [vert.normal[0], vert.normal[1], vert.normal[2]]
        v.texcoord = list(uv_map.get(i, (0.0, 0.0)))
        mesh.verts.append(v)
    mesh.numVerts = len(mesh.verts)

    # Build face list from triangulated mesh
    for lt in tri_mesh.loop_triangles:
        f = Face()
        f.data = list(lt.vertices)
        # Update per-face UV (more accurate than per-vertex average)
        if uv_layer:
            for j, (vi, li) in enumerate(zip(lt.vertices, lt.loops)):
                uv = uv_layer.data[li].uv
                mesh.verts[vi].texcoord = [uv[0], 1.0 - uv[1]]
        mesh.faces.append(f)
    mesh.numFaces = len(mesh.faces)

    bpy.data.meshes.remove(tri_mesh)

    # Bone / skinning links
    if len(item.vertex_groups) > 1:
        mesh.blend = True
        mesh.boneLink = -1
        for vg in item.vertex_groups:
            blList = blendedLinkGroup()
            blList.mesh = midx
            mdl.blendedLinks[-1].append(blList)
    elif len(item.vertex_groups) == 1:
        mesh.boneLink = mdl.find_bone(item.vertex_groups[0].name)
        print("Linked to bone " + str(mesh.boneLink))

    mdl.meshes.append(mesh)


def addSurf(mdl, item):
    if len(item.data.polygons) > 128:
        print('Warning: skipping surface ' + item.name + ', number of faces exceeds 128')
        return
    surf = surface_t()
    for poly in item.data.polygons:
        verts = item.data.vertices
        plane = plane_t()
        plane.normal.data = [poly.normal[0], poly.normal[1], poly.normal[2]]
        plane.distance = poly.normal.dot(verts[poly.vertices[0]].co)
        surf.planes.append(plane)
        surf.bmin.data = list(verts[poly.vertices[0]].co)
        surf.bmax.data = list(verts[poly.vertices[0]].co)
        for v in poly.vertices[1:]:
            for i in range(3):
                if verts[v].co[i] < surf.bmin.data[i]:
                    surf.bmin.data[i] = verts[v].co[i]
                if verts[v].co[i] > surf.bmax.data[i]:
                    surf.bmax.data[i] = verts[v].co[i]
    if len(surf.planes) > 3:
        mdl.surfs.append(surf)


def fromBlender(useSelection=False):
    mdl = model.S2Model()

    # Root bone (index 0, parent=-1)
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
        bn.base = matrix.fromBlenderMatrix(
            [list(i) for i in bone.matrix] +
            [[bone.head[0], bone.head[1], bone.head[2], 1.0]]
        )
        bn.invBase = matrix.matrix43_t()
        bn.idx = len(mdl.bones)
        bn.name = bone.name
        bn.parent = skel.bones.find(bone.parent.name) if bone.parent else -1
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
