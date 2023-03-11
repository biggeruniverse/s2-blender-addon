import os,sys

import bpy
from bpy_extras.image_utils import load_image
from bpy_extras import node_shader_utils

def meshToBlender(mesh, model):
    mesh_uvs = []
    blmesh = bpy.data.meshes.new(name=mesh.name)

    blmesh.vertices.add(mesh.numVerts)

    blmesh.vertices.foreach_set("co", [a for v in mesh.verts for a in (v.data[0], v.data[1], v.data[2])])

    loops = []
    faces_loop_start = []
    faces_loop_total = []
    lidx = 0
    for f in mesh.faces:
        mesh_uvs.extend([mesh.verts[i].texcoord for i in f.data])
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
        #mtex.use_map_color_diffuse = True

        blmesh.materials.append(material)
        #for face in blmesh.uv_textures[0].data:
        #    face.image = image

    return blmesh

def toBlender(model):
    for ob in bpy.context.selected_objects:
        ob.select_set(False)

    parent = bpy.data.objects.new("s2model", None)
    bpy.context.collection.objects.link(parent)
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)
    
    for m in model.meshes:
        mesh = bpy.data.objects.new(m.name, meshToBlender(m, model))
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


