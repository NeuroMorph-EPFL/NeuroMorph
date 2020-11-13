#    NeuroMorph (C) 2019,  Anne Jorstad
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/

bl_info = {  
    "name": "NeuroMorph Bounding Boxes",
    "author": "Anne Jorstad",
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > NeuroMorph > Bounding Boxes",
    "description": "Calculate the bounding boxes and primary axis lengths of a set of objects such as mitochondria",
    "wiki_url": "",
    "category": "Tool"}  
  
import bpy
from bpy.props import *
from mathutils import Vector, Matrix
import mathutils
import math
import os
import sys
import re
from os import listdir
import copy
import numpy as np  # must have Blender > 2.7
import datetime
from bpy_extras.io_utils import ExportHelper


# Define the panel
class NEUROMORPH_PT_BoundingBoxPanel(bpy.types.Panel):
    bl_idname = "NEUROMORPH_PT_BoundingBoxPanel"
    bl_label = "Bounding Boxes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeuroMorph"

    def draw(self, context):

        row = self.layout.row(align=True)
        row.prop(context.scene, "filename")
        row.operator("neuromorph.set_filename", text='', icon='FILEBROWSER')

        row = self.layout.row()
        row.operator("neuromorph.get_geometry", text='Get Bounding Boxes', icon='MESH_CUBE')

        # row = self.layout.row()
        # row.operator("neuromorph.get_geometry_single", text='Get Single Bounding Box', icon='MESH_CUBE')



# Tool to measure lengths/tubularities of many mitochondria objects in a scene
# 
# Separate input into distinct objects if input is single joined object
# Then calculate for each object:
# - length of major axis of bounding box
# - ratio of major axis length to mean of other 2 axis lengths
# - volume
class NEUROMORPH_OT_get_geometry(bpy.types.Operator):
    """Get bounding boxes of input object (can be several joined objects) or its childen"""
    bl_idname = "neuromorph.get_geometry"
    bl_label = "Get bounding boxes of input object (can be several joined objects) or its childen"

    def execute(self, context):
        # # Separate into distinct objects if input is single joined object
        # ob_list = [ob for ob in bpy.data.objects if ob.select_get() == True]
        # if len(ob_list) == 1:

        these_obs = [ob for ob in bpy.data.objects if ob.select_get() == True]
        if len(these_obs) != 1:
            infostr = "Please select exactly 1 object (with or without children)"
            self.report({'INFO'}, infostr)
            return {'FINISHED'}

        ob_orig = bpy.context.object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        name_orig = ob_orig.name
        if name_orig[-7:] == "_parent":
            name_orig = name_orig[0:-7]

        # Define material for bounding boxes
        if "transparent" in [mat.name for mat in bpy.data.materials]:
            mat_bb = bpy.data.materials["transparent"]
        else:
            this_color = (0.6,0.8,1.0, 0.25)
            this_alpha = 0.25
            mat_bb = add_unified_material(this_color, this_alpha, this_mat_name = "transparent")


        # Separate into distinct child objects if input has no children
        if len(ob_orig.children) == 0:
            t0 = datetime.datetime.now()

            # Store list of current objects
            ob_list_before = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']

            # Separate each discontiguous region into a separate object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.mesh.separate(type='LOOSE')

            # Remove all pre-existing objects to result in a list of just the newly separated objects
            ob_list_after = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
            for ob_i in ob_list_before:
                ob_list_after.remove(ob_i)

            ob_list_after.insert(0, bpy.data.objects[name_orig])
            ob_list = ob_list_after

            # Make new separated objects children of an empty parent object
            fullname_ob = name_orig + "_parent"
            # ob_parent = bpy.data.objects.new(fullname_ob, None)
            # bpy.context.scene.collection.objects.link(ob_parent)

            ob_parent = bpy.data.objects.new(fullname_ob, None)
            bpy.context.scene.collection.objects.link(ob_parent)
            update_collection_of_new_obj(ob_parent, ob_orig)

            for ob in ob_list:
                ob.parent = ob_parent

            # Create bounding box object
            fullname_bbox = "BBox_" + name_orig + "_parent"
            bbox_parent = bpy.data.objects.new(fullname_bbox, None)
            bpy.context.scene.collection.objects.link(bbox_parent)
            update_collection_of_new_obj(bbox_parent, ob_orig)

            t1 = datetime.datetime.now()
            print("time to separate: ", t1-t0)

        else:
            ob_parent = ob_orig
            ob_list = ob_parent.children
            fullname_bbox = "BBox_" + name_orig + "_parent"
            bbox_parent_list = [ob_i for ob_i in bpy.data.objects if ob_i.name == fullname_bbox]
            if bbox_parent_list == []:
                bbox_parent = bpy.data.objects.new(fullname_bbox, None)
                bpy.context.scene.collection.objects.link(bbox_parent)
                update_collection_of_new_obj(bbox_parent, ob_orig)
            else:
                bbox_parent = bbox_parent_list[0]


        t2 = datetime.datetime.now()

        # Loop through each object, extracting geometric info
        geom_props = []
        for ob in ob_list:
            # ob = bpy.data.objects[ob_name]
            print(ob.name)
            this_data = get_geom_properties(ob, bbox_parent, mat_bb)
            geom_props.append(this_data)  # [max_length, length_ratio, volume]

        ob_names = [ob.name for ob in ob_list]
        write_data(self, geom_props, ob_names)

        t3 = datetime.datetime.now()
        print("time to process: ", t3-t2)

        return {'FINISHED'}



# class NEUROMORPH_OT_get_geometry_single(bpy.types.Operator):
#     """Get geometry of single object"""
#     bl_idname = "neuromorph.get_geometry_single"
#     bl_label = "Get geometry of single object"

#     def execute(self, context):
#         ob_orig = bpy.context.object
#         name_orig = ob_orig.name

#         # Get bounding box parent object  <-- todo: not sure this is the desired behavior
#         fullname_bbox = "BBox_" + ob_name + "_parent"
#         bbox_parent = [ob_i for ob_i in bpy.data.objects if ob_i.name == fullname_bbox]
#         if bbox_parent == []:
#             bbox_parent = bpy.data.objects.new(fullname_bbox, None)
#             bpy.context.scene.collection.objects.link(bbox_parent)

#         this_data = get_geom_properties(ob_orig, bbox_parent)
#         # write_data(self, [this_data], [name_orig])
#         return {'FINISHED'}


def update_collection_of_new_obj(obj, scene_obj):
    # Add new obj to same collection as scene_obj
    these_collections = scene_obj.users_collection  # could be multiple
    default_collections = obj.users_collection
    for con in default_collections:
        con.objects.unlink(obj)
    for con in these_collections:
        con.objects.link(obj)


def get_geom_properties(ob, bbox_parent, mat_bb):

    # Process on convex hull?, fewer vertices
    # todo: is it better if keep the weighting of all the original vertices?
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Find primary axis via SVD decomposition
    # First center coords to origin, and subsample if too many vertices
    vert_coords_orig = [v.co for v in ob.data.vertices]
    max_verts = 20000  # To prevent memory errors in the svd call
    if len(vert_coords_orig) > max_verts:
        vert_coords_orig = subsample_points(vert_coords_orig, max_verts)
    centroid = Vector(np.mean(vert_coords_orig, axis = 0))
    vert_coords_centered = [v-centroid for v in vert_coords_orig]
    U, s, V = np.linalg.svd(vert_coords_centered)  # V[i] = eigenvector(i), normalized

    # Get rotation matrix (rotates data to be axis-aligned)
    rot_mat = Matrix.Identity(4)
    rot_mat[0][0:3] = V[0]
    rot_mat[1][0:3] = V[1]
    rot_mat[2][0:3] = V[2]

    # Get axis-aligned bounding box
    bbox_minmax = get_bounding_box(vert_coords_orig, rot_mat)  # rotates pts, finds bbox
    bbox = add_box(bbox_minmax, mat_bb)
    bbox.parent = bbox_parent

    # Give the bounding box the correctly indexed name
    name_split = ob.name.split(".")
    if len(name_split) == 2:
        bbox.name = "BBox." + name_split[1]
    else:
        bbox.name = "BBox " + name_split[0]

    # Rotate bbox back to object location
    rot_inv = Matrix(np.linalg.inv(rot_mat))
    for vv in bbox.data.vertices:
        vv.co = rot_inv @ vv.co

    # Get ordered box side lengths
    xrng = bbox_minmax[1] - bbox_minmax[0]
    yrng = bbox_minmax[3] - bbox_minmax[2]
    zrng = bbox_minmax[5] - bbox_minmax[4]
    len_max = max(xrng, yrng, zrng)
    len_min = min(xrng, yrng, zrng)

    # print(len_max, len_min, xrng, yrng, zrng)

    len_mid = [val for val in [xrng, yrng, zrng] if val != len_max and val != len_min][0]

    # Calculate length properties
    length_ratio = len_max / ((len_mid + len_min)/2)
    volume = get_vol(ob)  # This assumes a manifold surface

    bpy.ops.object.mode_set(mode='OBJECT')

    return([len_max, len_mid, len_min, length_ratio, volume])



def subsample_points(coords, max_verts):
    # For now, just sample regularly, in future should be smarter
    npts = len(coords)
    skip = math.ceil(npts / max_verts)
    coords = coords[0:-1:skip]
    return(coords)


def get_bounding_box(vert_coords, rot_mat):
    verts_rotated = [rot_mat@v for v in vert_coords]  # if rot_mat is V, bb is axis-aligned
    xs = [v[0] for v in verts_rotated]
    ys = [v[1] for v in verts_rotated]
    zs = [v[2] for v in verts_rotated]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))



def add_box(box_minmax, mat_bb):
    # box_minmax is either [xmin, xmax, ymin, ymax, zmin, zmax]
    #            or a vector containing all 8 vertex coordinates
    activate_an_object()
    bpy.ops.object.mode_set(mode='OBJECT')

    if len(box_minmax) == 6:
        box_verts = box_cords(box_minmax)
    elif len(box_minmax) == 8:
        box_verts = box_minmax
    else:
        print("unrecognized input!")
        return()
    bpy.ops.mesh.primitive_cube_add(location=[0,0,0])
    new_cube = bpy.context.object
    for ii, vv in enumerate(box_verts):
        new_cube.data.vertices[ii].co = vv
    # Make transparent
    new_cube.active_material = mat_bb
    return(new_cube)


def box_cords(box_minmax):
    # Returns vertices in same configuration as Blender cube
    cords = [Vector((box_minmax[0],box_minmax[2],box_minmax[4])),
             Vector((box_minmax[0],box_minmax[2],box_minmax[5])),
             Vector((box_minmax[0],box_minmax[3],box_minmax[4])),
             Vector((box_minmax[0],box_minmax[3],box_minmax[5])),
             Vector((box_minmax[1],box_minmax[2],box_minmax[4])),
             Vector((box_minmax[1],box_minmax[2],box_minmax[5])),
             Vector((box_minmax[1],box_minmax[3],box_minmax[4])),
             Vector((box_minmax[1],box_minmax[3],box_minmax[5]))]
    return cords



def get_vol(ob):
    activate_an_object()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob

    # Detect any open holes and add faces
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.edge_face_add()

    # Convert all faces to triangles (necessary for volume calculation)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Loop through each face
    n_faces = len(ob.data.polygons)
    vol = 0
    for ff in range(0, n_faces):
        this_face = ob.data.polygons[ff]
        n_vertices = len(this_face.vertices[:])
        if n_vertices != 3:
            print("faces must be triangles!  " + str(ff))
        tri = [0] * n_vertices
        for vv in range(0, n_vertices):
            tri[vv] = ob.data.vertices[ob.data.polygons[ff].vertices[vv]].co
        vol += get_vol_tri(tri)
    return(vol)

def get_vol_tri(tri):  
    # tri = [p0, p1, p2],  pn = [x, y, z]
    p0 = tri[0]
    p1 = tri[1]
    p2 = tri[2]
    vcross = cross_product(p1,p2)
    vdot = dot_product(p0, vcross)
    vol = vdot/6
    return vol

def cross_product(v0, v1):  # faster than numpy
    x =   v0[1]*v1[2] - v0[2]*v1[1]
    y = -(v0[0]*v1[2] - v0[2]*v1[0])
    z =   v0[0]*v1[1] - v0[1]*v1[0]
    return [x,y,z]


def dot_product(v0,v1):
    vec = [v0[n]*v1[n] for n in range(len(v0))]
    return sum(vec)



# Create material whose diffufe color and alpha in Solid display and 
# BSDF node color and alpha in Material Preview display are linked
# This function and the following are direct copies from NeuroMorph_3D_Drawing
def add_unified_material(this_color, this_alpha, this_mat = None, this_mat_name = "new material"):
    # if this_mat is None:
    if this_mat is None or this_mat.node_tree is None or "Principled BSDF" not in this_mat.node_tree.nodes:
        this_mat = bpy.data.materials.new(this_mat_name)
        this_mat.use_nodes = True
        this_mat.name = this_mat_name

    # For Solid display
    this_color_transparent = list(this_color)
    this_color_transparent[3] = this_alpha
    this_mat.diffuse_color = this_color_transparent

    # For Material Preview display (preferred, as image textures are visible here)
    this_mat.use_nodes = True
    BSDF_node = this_mat.node_tree.nodes["Principled BSDF"]
    BSDF_node.inputs["Base Color"].default_value = this_color
    BSDF_node.inputs["Alpha"].default_value = this_alpha
    this_mat.blend_method = 'BLEND'

    # Attach the BSDF node to the diffuse color, so they change together
    # And so alpha progresses from invisible to opaque in all modes
    attach_color_driver(this_mat, 0)
    attach_color_driver(this_mat, 1)
    attach_color_driver(this_mat, 2)
    attach_color_driver(this_mat, 3)

    return(this_mat)

# Attach BSDF node to the viewport display (diffuse color) for smooth alpha slider 
# and same color between display modes (ind is color channel: {0,1,2} for rbg, 3 for alpha)
# from: https://blender.stackexchange.com/questions/185105/
#       single-slider-for-transparency-in-material-preview-rendered-display/185117#185117
def attach_color_driver(this_mat, ind):
    if ind == 3:
        alpha_input = this_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"]  # Store access to the alpha input
        driver = alpha_input.driver_add("default_value").driver  # Create a new driver and store it
    else:
        color_input = this_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        driver = color_input.driver_add("default_value", ind).driver

    [driver.variables.remove(value) for value in reversed(driver.variables.values())]
    var = driver.variables.new()
    target = var.targets[0]
    target.id_type = 'MATERIAL'
    target.id = this_mat
    target.data_path = "diffuse_color[" + str(ind) + "]"
    driver.expression = "var"





# Define file name and path for export
class NEUROMORPH_OT_set_filename(bpy.types.Operator, ExportHelper):
    """Define file name and path for distance measurement export"""
    bl_idname = "neuromorph.set_filename"
    bl_label = "Define file path and name"

    filename_ext = ".csv"  # ExportHelper mixin class uses this
    def execute(self, context):
        full_filename = self.filepath
        bpy.context.scene.filename = full_filename
        return {'FINISHED'}


# Write data to file, assumes geom_props and ob_names are same length
def write_data(self, geom_props, ob_names):
    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")
    full_filename = bpy.context.scene.filename

    f = open(full_filename, 'w')
    f.write("Object Name;Max Length of Bounding Box;Mid Length;Min Length;Ratio max/mean(mid+min);Volume of Contained Object\n")

    # Write data for each bounding box
    for ii, elt in enumerate(geom_props):
        [max_len, mid_len, min_len, rat_len, vol] = elt
        f.write(ob_names[ii] + ";" + str(max_len) + ";" + str(mid_len) + ";" + \
            str(min_len) + ";" + str(rat_len) + ";" + str(vol) +"\n")

    # Also calculate summary statistics
    max_lens = [v[0] for v in geom_props]
    mid_lens = [v[1] for v in geom_props]
    min_lens = [v[2] for v in geom_props]
    rat_lens = [v[3] for v in geom_props]
    vols = [v[4] for v in geom_props]

    f.write("\nMean;" + str(np.mean(max_lens)) + ";" + str(np.mean(mid_lens)) + ";" + \
        str(np.mean(min_lens)) + ";" + str(np.mean(rat_lens)) + ";" + str(np.mean(vols)) + "\n")
    f.write("Median;" + str(np.median(max_lens)) + ";" + str(np.median(mid_lens)) + ";" + \
        str(np.median(min_lens)) + ";" + str(np.median(rat_lens)) + ";" + str(np.median(vols)) + "\n")
    f.close()
    self.report({'INFO'}, "Finished exporting file.")





# Sometimes this is necessary before changing modes
def activate_an_object(ob_0=[]):
    # tmp = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide_get() == False][0]
    # bpy.context.view_layer.objects.active = tmp  # required before setting object mode

    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    if ob_0 == []:
        ob_0 = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide_get() == False][0]
    bpy.context.view_layer.objects.active = ob_0
    ob_0.select_set(True)



def register():
    register_classes()

    # Define scene variables
    bpy.types.Scene.filename = bpy.props.StringProperty \
    (
        name = "Output file", 
        description = "Set file name and path for output data", 
        default = "/"
    )


def unregister():
    unregister_classes()
    del bpy.types.Scene.filename


classes = (
    NEUROMORPH_PT_BoundingBoxPanel,
    NEUROMORPH_OT_set_filename,
    NEUROMORPH_OT_get_geometry
)
register_classes, unregister_classes = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
