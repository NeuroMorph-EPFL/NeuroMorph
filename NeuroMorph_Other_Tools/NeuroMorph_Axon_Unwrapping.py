#    NeuroMorph_Axon_Unwrapping.py (C) 2019,  Anne Jorstad
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
    "name": "NeuroMorph Axon Unwrapping",
    "author": "Anne Jorstad",
    "version": (0, 1, 0),
    "blender": (2, 7, 9),
    "location": "View3D > NeuroMorph > Axon Unwrapping",
    "description": "Unwrap axons using tools from the Centerline addon",
    "warning": "",  
    "wiki_url": "",  
    "tracker_url": "",  
    "category": "Tool"}  
  
import bpy
from bpy.props import *
from mathutils import Vector  
import mathutils
import math
import os
import sys
import re
from os import listdir
import copy
import numpy as np  # must have Blender > 2.7
import csv
import xml.etree.ElementTree as ET
import datetime
import pickle
import bmesh


# Note: The vast majority of the code in this addon is a near-direct copy from NeuroMorph_Centerline_Processing, 
#       with sections from NeuroMorph_Measurement_Tools.  All classes have been renamed with "_unwrap" so as not
#       to conflict with their original versions.  
#       The main differences are the addition of a yaxis object that gets carried through the centerline 
#       processing tools (must exist before calculating the cross-sections), and then the new functions to 
#       setup and perform the vesicle projections onto the cross-section boundary points.


# Define the panel
class UnwrappingPanel(bpy.types.Panel):
    bl_label = "Axon Unwrapping"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "NeuroMorph"

    def draw(self, context):

        row = self.layout.row()
        row.operator("object.preprocess_mesh_unwrap", text='Clean Mesh for Processing', icon='MESH_UVSPHERE')

        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.operator("object.close_mesh_unwrap", text='If mesh is open, close open mesh', icon='MESH_UVSPHERE')

        row = self.layout.row()
        row.operator("object.length_on_mesh_unwrap", text = "Define y-axis from 2 points", icon="CURVE_NCURVE")

        row = self.layout.row()
        row.operator("object.update_centerline_unwrap", text='Setup Centerline', icon='MOD_CURVE')

        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "search_radius")

        row = self.layout.row()
        row.operator("object.get_surface_areas_unwrap", text='Get Cross-sectional Surface Areas', icon='FACESEL_HLT')

        row = self.layout.row()
        row.operator("object.project_vesicles_unwrap", text='Project Spheres to Centerline', icon="FULLSCREEN_EXIT")

        row = self.layout.row()
        row.operator("object.setup_surf_proj_unwrap", text='Setup Surface Projection', icon="OUTLINER_OB_CURVE")

        row = self.layout.row()
        row.operator("object.project_to_surf_unwrap", text='Project Spheres to Surface', icon="FULLSCREEN_EXIT")

        row = self.layout.row()
        row.operator("object.project_syn_to_surf_unwrap", text='Project Synapse to Surface', icon="FULLSCREEN_EXIT")




###############################################################################################
# Copied from NeuroMorph_Measurement_Tools
###############################################################################################
class PathOnMesh_unwrap(bpy.types.Operator):
    """Shortest path between two points through vertices on the mesh (input: 2 selected vertices on mesh)"""
    bl_idname = "object.length_on_mesh_unwrap"
    bl_label = "Create Shortest Path connecting two selected vertices"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.object
        vert_inds = [vind for vind, vert in enumerate(obj.data.vertices) if vert.select == True]
        if len(vert_inds)==2:

            # Temporarily add edges to connect vertices across each face
            add_face_edges_unwrap(obj, vert_inds)

            # Select the shortest path on the mesh (does above)
            select_shortest_path_unwrap(obj, vert_inds, self)

            # Create new object from selected points
            curve = new_obj_from_selected_verts_unwrap(obj)
            curve.name = "yaxis"
            bpy.context.scene.yaxis_name = "yaxis"  # set y-axis to this object

            # Undo the triangulate operation
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.ed.undo()

            activate_new_curve_unwrap(curve, obj)

            # Reorder vertices along curve to run from 0 to nverts
            bpy.ops.object.convert(target='CURVE')
            bpy.ops.object.convert(target='MESH')

        else:
            self.report({'INFO'},"Select exactly two points on mesh")
            obj.select=True
            bpy.context.scene.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
        return{'FINISHED'}


def select_shortest_path_unwrap(obj, vinds, self):
    # Select shortest path on obj between the (2) vertices with indices in vinds
    select_obj_unwrap(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for vind in vinds:
        obj.data.vertices[vind].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    err = bpy.ops.mesh.shortest_path_select()  
    bpy.ops.object.mode_set(mode='OBJECT')

    if "CANCELLED" in err:
        self.report({'INFO'},"Cannot calculate path: points are from disconnected parts of the mesh")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.ed.undo()
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select=True
        bpy.context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        return{'FINISHED'}

    # shortest_path_select() returns nothing if points are neighbors, so select them again
    verts_out = [v for v in obj.data.vertices if v.select == True]
    if len(verts_out) == 0:
        for vind in vinds:
            obj.data.vertices[vind].select = True



def add_face_edges_unwrap(obj, vert_inds):
# add edges to connect vertices on each face across the face:
# for each quadrilateral face, add the two diagonals,
# for each n>4-sided face, add the centroid and edges connecting
# it to each original vertex,
# leave triangular faces as they are

    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    data = obj.data
    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(data)   # fill it in from a Mesh

    # find shortest path using centroids of all faces;
    # only add diagonal edges to quad faces that include
    # vertices from this shortest path
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.poke()  # adds the centroid to each face and radial edges connecting it each vertex
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for vind in vert_inds:
        data.vertices[vind].select=True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.shortest_path_select()
    bpy.ops.object.mode_set(mode='OBJECT')

    # store the indices of these vertices, then undo, then proceed
    poke_path_inds = []
    for v in data.vertices:
        if v.select:
            poke_path_inds.append(v.index)
    # undo poke
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.ed.undo()
    bpy.ops.object.mode_set(mode='OBJECT')

    # handle quad faces
    bm.verts.ensure_lookup_table()
    for face in data.polygons:
        if len(face.vertices) == 4:
            on_path_flag = 0
            for vert in face.vertices:
                if vert in poke_path_inds:
                    on_path_flag = 1
                    break
            if on_path_flag:
                v0bm = bm.verts[face.vertices[0]]
                v1bm = bm.verts[face.vertices[1]]
                v2bm = bm.verts[face.vertices[2]]
                v3bm = bm.verts[face.vertices[3]]
                e1 = [v0bm, v2bm]
                e2 = [v1bm, v3bm]
                bm.edges.new(e1)
                bm.edges.new(e2)
    bm.edges.index_update()
    bpy.ops.object.mode_set(mode='OBJECT')
    bm.to_mesh(data)
    bpy.ops.object.mode_set(mode='EDIT')

    # handle non-quad faces  (leave triangular faces as they are)
    # if many faces with >4 sides might be slow
    for face in bm.faces:  # use the bmesh data structure: pointers don't go away after context change
        if len(face.verts) > 4:
            bpy.ops.mesh.select_all(action='DESELECT')
            face.select = True
            bpy.ops.object.mode_set(mode='OBJECT')
            bm.to_mesh(data)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.poke()

    bm.edges.index_update()
    bmesh.update_edit_mesh(data, destructive=True)  # to update mesh in scene
    bm.free()

def get_total_length_of_edges_unwrap(ob):
    # Get length of all elected edges on an object
    # Assign total length to scene variable

    # # Convert to global coordinates, just in case this hasn't already been done
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Get length of all edges
    bpy.ops.object.mode_set(mode='EDIT')
    select_as_vert = tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1]
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.object.mode_set(mode='OBJECT')
    edges = [ed for ed in ob.data.edges if ed.select == True]

    total_len = 0
    for ed in edges:
        v1 = ob.data.vertices[ed.vertices[0]].co
        v2 = ob.data.vertices[ed.vertices[1]].co
        total_len += (v1-v2).length

    if not select_as_vert:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.object.mode_set(mode='OBJECT')

    return(total_len)

def new_obj_from_selected_verts_unwrap(obj):
    obs0 = [ob.name for ob in bpy.context.scene.objects]

    obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.duplicate_move()
    bpy.ops.mesh.separate(type='SELECTED')

    # select the newly created object
    obs1 = [ob.name for ob in bpy.context.scene.objects]
    new_ob_name = [o1 for o1 in obs1 if o1 not in obs0][0]  # the newly created object
    new_obj = bpy.context.scene.objects[new_ob_name]
    return (new_obj)

def activate_new_curve_unwrap(curve, obj):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    curve.select=True
    bpy.context.scene.objects.active = curve
    curve.show_wire = True  # Show curve on top of mesh for better display
    curve.parent = obj  # Assign curve to be child of parent object

###############################################################################################
# End: Copied from NeuroMorph_Measurement_Tools
###############################################################################################



class PreProcessMesh_unwrap(bpy.types.Operator):
    """Remove and fill non-manifold mesh geometry of selected mesh"""
    bl_idname = "object.preprocess_mesh_unwrap"
    bl_label = "Clean non-manifold mesh geometry"

    def execute(self, context):
        mesh = bpy.context.object

        # De-select all vertices
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")

        while (True):
            bpy.ops.mesh.select_all(action='DESELECT')

            # Select non-manifold vertices
            bpy.ops.mesh.select_non_manifold()

            # If no non-manifold points, check for hanging faces not detected by manifold tool
            bpy.ops.object.mode_set(mode='OBJECT')
            selected = [v for v in mesh.data.vertices if v.select]
            if len(selected) == 0:

                # Remove any vertices attached to <= 2 faces
                vert_table = faces_per_vertex_unwrap(mesh)
                hanging_v_inds = [ind for ind, val in enumerate(vert_table) if val <= 2]

                # If all vertices are acceptable, exit loop
                if len(hanging_v_inds) == 0:
                    break
                else:
                    for ind in hanging_v_inds:
                        mesh.data.vertices[ind].select = True


            # Ensure vertex 0 is not about to be deleted (used later with select_linked)
            if mesh.data.vertices[0].select:
                print("Warning: about to delete vertex 0!")
            bpy.ops.object.mode_set(mode='EDIT')

            # Delete bad vertices
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()

            # Delete regions that have been disconnected from the main mesh
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh.data.vertices[0].select = True  # this better be part of the main mesh!
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_linked()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

            # Fill removed holes
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.edge_face_add()

        # Divide newly added faces into planar polys
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.object.mode_set(mode='OBJECT')
        big_faces = [f for f in mesh.data.polygons if len(f.vertices) > 4]
        for f in big_faces:
            f.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.vert_connect_nonplanar(angle_limit=0)
        bpy.ops.mesh.select_mode(type="VERT")

        # Return mesh in edit mode with fixed regions highlighted
        return {'FINISHED'}


# Close open mesh, 
# Necessary for check in update_centerline to see if centerline endpoints are inside mesh 
class CloseOpenMesh_unwrap(bpy.types.Operator):
    """Close any holes in mesh"""
    bl_idname = "object.close_mesh_unwrap"
    bl_label = "Close open mesh"

    def execute(self, context):
        mesh = bpy.context.object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


# Count the number of faces each vertex is a part of
def faces_per_vertex_unwrap(ob):
    faces = ob.data.polygons
    vert_table = len(ob.data.vertices) * [0]
    for f in faces:
        for v in f.vertices:
            vert_table[v] += 1
    return vert_table


class RedefineCenterline_unwrap(bpy.types.Operator):
    """Use selected centerline with selected mesh object (initializes all centerline properties)"""
    bl_idname = "object.update_centerline_unwrap"
    bl_label = "Use modified centerline"

    def execute(self, context):
        err, objs = assign_selected_objects_unwrap(self)
        if err < 0:
            return {'FINISHED'}
        centerline, meshobj = objs

        # Check if centerline has been modified by hand
        unmodified = False  # not using this concept for unwrapping
        nverts = len(centerline.data.vertices)

        # Instantiate data containers
        if not hasattr(centerline, 'centerline_min_radii'):
            centerline["centerline_min_radii"] = []
        if not hasattr(centerline, 'cross_sectional_areas'):
            centerline["cross_sectional_areas"] = []
        if not hasattr(centerline, 'centerline_max_radii'):
            centerline["centerline_max_radii"] = []
        if not hasattr(centerline, 'vesicle_counts'):
            centerline["vesicle_counts"] = []
        if not hasattr(centerline, 'area_sums'):
            centerline["area_sums"] = []
        if not hasattr(centerline, 'vesicle_list'):
            centerline["vesicle_list"] = []
        if not hasattr(centerline, 'yaxis_pts'):
            centerline["yaxis_pts"] = []
        if not hasattr(centerline, 'yaxis_inds'):
            centerline["yaxis_inds"] = []


        # Remove any centerline points that are outside obj
        inds_to_check = [nverts-1, nverts-2, nverts-3, 0, 1, 2]
        inds_to_delete = []
        for ind in inds_to_check:
            coord = centerline.data.vertices[ind].co
            if point_outside_mesh_unwrap(coord, meshobj):
                inds_to_delete += [ind]

        activate_an_object_unwrap(centerline)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for ind in inds_to_delete:
            centerline.data.vertices[ind].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')

        print("inds to delete")
        print(inds_to_delete)

        # Reorder vertices along curve to run from 0 to nverts
        activate_an_object_unwrap(centerline)
        bpy.ops.object.convert(target='CURVE')
        bpy.ops.object.convert(target='MESH')
        meshobj.select = True  # Return centerline and mesh selected, for next tool

        # # Reassign number of centerline points: not using scene variables here
        # nverts = len(centerline.data.vertices)
        # bpy.context.scene.npts_centerline = nverts

        return {'FINISHED'}



# Check if point is inside object
def point_outside_mesh_unwrap(coord, ob):
    # if rays in all 6 directions from pt intersect ob, assume pt is inside ob, else is outside
    axes = [ mathutils.Vector((1,0,0)), mathutils.Vector((0,1,0)), mathutils.Vector((0,0,1)), \
             mathutils.Vector((-1,0,0)), mathutils.Vector((0,-1,0)), mathutils.Vector((0,0,-1)) ]
    coord = mathutils.Vector(coord)
    max_dist = 10000.0
    count = 0
    for axis in axes:  # send out rays, if cross this object in every direction, point is inside
        result,location,normal,index = ob.ray_cast(coord, coord+axis*max_dist)  # will error if ob in different layer
        if index != -1:
            count += 1
    if count < 6:
        return True
    else:
        return False



# Extract centerline and mesh object from selected objects (exactly 2 selected objects expected)
# Perform basic sanity checks
def assign_selected_objects_unwrap(self):
    these_obs = [ob for ob in bpy.data.objects if ob.select == True]
    if len(these_obs) != 2:
        infostr = "Must select exactly 2 objects:  1 centerline and 1 surface mesh"
        self.report({'INFO'}, infostr)
        return(-1, [])
    centerline = [ob for ob in these_obs if len(ob.data.polygons) == 0]
    mesh_obj = [ob for ob in these_obs if len(ob.data.polygons) > 0]
    if len(centerline) == 0:
        infostr = "No centerline object selected (expecting curve, but faces detected)"
        self.report({'INFO'}, infostr)
        return(-1, [])
    if len(centerline) > 1:
        infostr = "Detected more than 1 potential centerline; second object must contain faces"
        self.report({'INFO'}, infostr)
        return(-1, [])
    centerline = centerline[0]
    mesh_obj = mesh_obj[0]
    return(0, [centerline, mesh_obj])


class GetSurfaceAreas_unwrap(bpy.types.Operator):
    """Get cross sectional areas from selected centerline and axon (input: 2 objects)"""
    bl_idname = "object.get_surface_areas_unwrap"
    bl_label = "Get cross sectional areas from selected centerline and axon"

    def execute(self, context):

        # Extract centerline and mesh object from selected objects (exactly 2 selected objects expected)
        # centerline, meshobj = assign_selected_objects_unwrap(self)
        err, objs = assign_selected_objects_unwrap(self)
        if err < 0:
            return {'FINISHED'}
        centerline, meshobj = objs

        # Project objects so 3D coordinates are consistent
        convert_to_global_coords_unwrap()

        # Preconstruct kd tree to aid in trimming far away vertices (fast)
        nverts_mesh = len(meshobj.data.vertices)
        kd_mesh = mathutils.kdtree.KDTree(nverts_mesh)
        for i1, v1 in enumerate(meshobj.data.vertices):
            kd_mesh.insert(v1.co, i1)
        kd_mesh.balance()

        # Define material for cross sectional area slices
        mat = bpy.data.materials.new("cross_section_material")
        mat.diffuse_color = (0.0,1.0,1.0)

        # Iterate down centerline
        bpy.context.scene.parallel_xsections = True  # Must be true for unwrapping
        parallel_xsections = bpy.context.scene.parallel_xsections
        if parallel_xsections:
            yaxis_pts = []
            yaxis_inds = []

        cross_section_names = []
        areas = []
        t0 = datetime.datetime.now()
        for ind in range(0, len(centerline.data.vertices)):
            print(ind)
            this_xsection_name, this_area, this_yaxis_pt, this_yaxis_ind = get_cross_section_unwrap(centerline, ind, meshobj, kd_mesh, self)
            cross_section_names.append(this_xsection_name)
            areas.append(this_area)
            if parallel_xsections:
                    yaxis_pts.append(this_yaxis_pt)
                    yaxis_inds.append(this_yaxis_ind)
        t3 = datetime.datetime.now()
        print("total time: ", t3-t0)

        # Add areas to centerline object
        centerline["cross_section_names"] = cross_section_names
        centerline["cross_sectional_areas"] = areas

        if parallel_xsections:
            centerline["yaxis_pts"] = yaxis_pts
            centerline["yaxis_inds"] = yaxis_inds

        return {'FINISHED'}


# Define normal of entire centerline to be direction 
# from first vertex to last vertex
# Used for parallel cross sections
def get_norm_centerline_unwrap(centerline):
    p_start = centerline.data.vertices[0].co
    p_end = centerline.data.vertices[-1].co
    norm_here = p_end-p_start
    return(norm_here)




########################### copied from updated centerline processing #######################################
def get_cross_section_unwrap(centerline, ind, meshobj, kd_mesh, self):
# Create perpindicular plane to centerline at ind
# Normal is weighted average of two prior and two next normals
# Get area of intersection of plane with mesh

    nverts_not_enough = 8  # had case where needed at least 7


    ######################### copied from old ###
    parallel_xsections = bpy.context.scene.parallel_xsections
    if parallel_xsections:
        # Assign same normal to all cross sections
        norm_here = get_norm_centerline_unwrap(centerline)
    else:
        norm_here = []

    plane = make_plane_unwrap(centerline, ind, norm_here)  # this is different from new function
    select_obj_unwrap(plane)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # select_obj_unwrap(meshobj)
    # bpy.ops.object.duplicate()
    # cross_section = bpy.context.object
    # select_obj_unwrap(cross_section)

    if parallel_xsections:
        yaxis_pt, yaxis_ind = get_yaxis_pt_unwrap(plane, norm_here, centerline, ind, self)
    else:  
        yaxis_pt = []
        yaxis_ind = []
    #########################################



    # plane = make_plane(centerline, ind)  # Normal is weighted average of two prior and two next normals
    # select_obj_unwrap(plane)
    # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    select_obj_unwrap(meshobj)
    bpy.ops.object.duplicate()
    cross_section = bpy.context.object
    select_obj_unwrap(cross_section)
    ctrline_vert = centerline.data.vertices[ind].co

    # # for debugging
    # cross_section = bpy.context.object
    # kd_mesh = mathutils.kdtree.KDTree(len(cross_section.data.vertices))
    # for i1, v1 in enumerate(cross_section.data.vertices):
    #     kd_mesh.insert(v1.co, i1)
    # 
    # kd_mesh.balance()

    # Delete vertices far away from centerline point
    delete_far_away_points = False
    if delete_far_away_points:
        rad = bpy.context.scene.search_radius  # distance is arbitrary
        close_pts = kd_mesh.find_range(ctrline_vert, rad)  # max_rad*4
        if len(close_pts) > 100:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type="VERT")  # need to be in vertex select mode for this to work
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for cp in close_pts:
                ind = cp[1]  # vector, ind, dist
                cross_section.data.vertices[ind].select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
            select_obj_unwrap(cross_section)
        else:
            print("found ", str(len(close_pts)), " close points, expecting more;  deleting nothing")
            x = crash  # deliberatly crash

    bpy.ops.object.duplicate()
    cross_section_backup = bpy.context.object
    select_obj_unwrap(cross_section)

    # Cut mesh at plane, create new cross sectional face (can take a couple seconds)
    print("trying first thresh")
    thresh = 1e-5
    apply_intersect_unwrap(cross_section, plane, thresh = thresh)

    # The bool_mod.double_threshold variable is finicky, and sometimes several values must be tried,
    # with bad cases returning a small number of edges instead of a cross-section
    if not cross_section_check_passed_unwrap(cross_section, cross_section_backup, nverts_not_enough):
        no_intersect_area = True
        thresh /= 10
        while (no_intersect_area):
            print("bad threshold? trying new threshold =", str(thresh))
            # Delete incorrect intersection object
            select_obj_unwrap(cross_section)
            bpy.ops.object.delete() 
            cross_section = cross_section_backup
            select_obj_unwrap(cross_section)
            # Copy a new backup object
            bpy.ops.object.duplicate()
            cross_section_backup = bpy.context.object
            select_obj_unwrap(cross_section)
            # Try a smaller threshold
            apply_intersect_unwrap(cross_section, plane, thresh = thresh)
            
            # Test all thresholds 1e-2 to 1e-10
            if thresh < 1e-10:
                thresh = 1e-4
            elif thresh >= 1e-4:
                thresh *= 10
            else:
                thresh /= 10

            if cross_section_check_passed_unwrap(cross_section, cross_section_backup, nverts_not_enough) or thresh > 1e-2:
                if thresh < 1e-2:
                    print("test passed with thresh =", str(thresh))
                    select_obj_unwrap(cross_section_backup)
                    bpy.ops.object.delete() 
                    select_obj_unwrap(cross_section)
                else:
                    print("found no appropriate threshold, code will intentionally error")
                    # This is likely a result of the mesh having non-manifold geometry
                    # Keep cross_section_backup for inspection
                    # todo: decide with users if they would prefer the code not to break, and instead 
                    #       simply have a missing cross-section. Unsafe for later analysis.
                    x = break_code

                no_intersect_area = False  # end the while loop
                # If this is never reached although the if statement was entered, code will intentionally error later

    else:
        select_obj_unwrap(cross_section_backup)
        bpy.ops.object.delete() 
        select_obj_unwrap(cross_section)



    # # This second modifier isn't working; instead find the intersecting face  
    # # by searching for the polygon with the most vertices
    # bool_mod = cross_section.modifiers.new('modifier2', 'BOOLEAN')
    # bool_mod.operation = 'DIFFERENCE'
    # bool_mod.object = plane
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier2')


    # Find area of new face with lots of verts
    # cap_inds = []
    big_poly_inds = []
    polys = cross_section.data.polygons
    for f_ind in range(0, len(polys)):
        this_face = polys[f_ind]
        if len(this_face.vertices) > nverts_not_enough:  # the cutting plane causes some quads to now have 5 edges, +1 for good measure
            big_poly_inds.append(f_ind)


    # polys = cross_section.data.polygons
    # npolys = len(polys)
    # bpinds = [ii for ii in range(0,npolys) if len(polys[ii].vertices) > nverts_not_enough]
    # print("number of big polys agrees?")
    # print(big_poly_inds == bpinds)


    if len(big_poly_inds) == 1:
        # cap_ind = big_poly_inds[0]
        cap_inds = big_poly_inds


    elif len(big_poly_inds) > 1:
        print("Warning:  " + str(len(big_poly_inds)) + " polys with > 6 verts, making selection")
        # This can happen when axon bends with high curvature and the plane intersects the mesh twice,
        # or if there is a hole in the cross section, as individual faces cannot have holes, 
        # or if geometry is strange and the entire plane is kept:
        # find face closest to this centerline point;
        # if there is a hole, also find the other part of the cross section on the other side of the hole

        # Remove any faces that contains points on the original plane
        plane_verts = [v.co for v in plane.data.vertices]
        remove_inds = []
        break_flag = False
        for c_ind in big_poly_inds:
            break_flag = False
            for v_ind in polys[c_ind].vertices:
                if not break_flag:
                    this_vert = cross_section.data.vertices[v_ind].co
                    if any(get_dist_unwrap(this_vert, pv) == 0 for pv in plane_verts):
                        remove_inds.append(c_ind)
                        break_flag = True
        for bad_ind in remove_inds:
            big_poly_inds.remove(bad_ind)

        # Save the face closest to the centerline point
        min_dist = 1000
        cap_ind = -1
        for c_ind in big_poly_inds:
            this_dist = get_dist_unwrap(ctrline_vert, polys[c_ind].center)
            if this_dist < min_dist:
                min_dist = this_dist
                cap_ind = c_ind
        #print("chose face with center at ", polys[cap_ind].center)
        # this_area = polys[cap_ind].area
        
        # If cross section has a hole, the found cross section poly will not be complete, 
        # as single faces cannot have holes; check if there is another poly with >6 verts 
        # that shares at least 2 edges with found poly
        other_inds = [ii for ii in big_poly_inds if ii != cap_ind]
        cap_edges = polys[cap_ind].edge_keys
        cap_inds = [cap_ind]
        for o_ind in other_inds:
            poly2_edges = polys[o_ind].edge_keys
            overlapping_edges = set(poly2_edges).intersection(set(cap_edges))
            if len(overlapping_edges) >= 2:  # There is a hole, join this face!
                cap_inds.append(o_ind)
        # Now cap_inds is a list of >= 1 face index
        

    else:
        print("ERROR:  found no appropriate polys with > 6 verts, something went wrong <-- investigate")
        print(len(big_poly_inds), "/", len(cross_section.data.polygons))
        x = intentional_crash_no_cross_section_found  # force crash

    # Create new object as child object of centerline
    new_face_ob = new_obj_from_polys(cross_section, cap_inds)
    new_face_ob.parent = centerline
    this_name = new_face_ob.name + str(ind)
    new_face_ob.name = this_name

    # Calculate area
    this_area = sum(polys[ii].area for ii in cap_inds)

    # Delete temporary plane object and mesh objects
    select_obj_unwrap(plane)
    bpy.ops.object.delete()
    select_obj_unwrap(cross_section)
    bpy.ops.object.delete()

    # return(this_area, new_face_ob)
    return(this_name, this_area, yaxis_pt, yaxis_ind)  # todo: return new_face_ob, not just it's name (as in newer vsn of code)


def cross_section_check_passed_unwrap(cross_section, cross_section_backup, nverts_not_enough = 8):
# Return true if cross_section meets criteria to be an actual cross section
# Does not currently check for a max number of points

    # Delete vertices and edges not part of any face
    select_obj_unwrap(cross_section)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for poly in cross_section.data.polygons:
        poly.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Check if no cross-sectional area created
    c1 = len(cross_section.data.polygons) > 0 
    if c1:

        # Check that a cross section poly exists
        poly_sizes = [len(poly.vertices) for poly in cross_section.data.polygons]
        max_ngon = max(poly_sizes)
        c2 = max_ngon > nverts_not_enough
        print("  inside check, nverts max_ngon =", max_ngon)

        # print(c1, c2)
        condition_met = c1 and c2

        # # Check if all vertices are co-planar
        # coords = np.array([v.co for v in cross_section.data.vertices])
        # coords_centered = coords - np.mean(coords, axis = 0)
        # cov = np.cov(coords_centered, rowvar = False)
        # evals, evecs = np.linalg.eig(cov)
        # min_eval = min(evals)
        # min_eval_coplanar = 1e-5  # with no numerical error, min eigenvalue should be 0 if all vertices are coplanar
        # c3 = min_eval < min_eval_coplanar

        # # Check that cross section is not just a big piece of the mesh, should use co-planar check instead
        # c3 = len(cross_section.data.polygons) < 10  # might limit number of possible holes to 9? 

        # Check if not enough vertices to be meaningful
        # c2 = len(cross_section.data.vertices) > nverts_not_enough

        # Must meet all conditions
        # condition_met = c1 and c2 and c3

    else:
        condition_met = False
    return (condition_met)


def apply_intersect_unwrap(obj, plane, thresh = .0001):
# Cut mesh at plane, create new cross sectional face (can take a couple seconds)
# The "carve" option will be removed in future versions of Blender, don't user it
    select_obj_unwrap(obj)
    bool_mod = obj.modifiers.new('modifier1', 'BOOLEAN')
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = plane
    bool_mod.double_threshold = thresh  # .0001? .00001? emperical; default e-7 sometimes returns just a few edges
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier1')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')

def new_obj_from_polys(cross_section, cap_inds):
    # Create new cross-section object, often a single face (but not necessarily)
    select_obj_unwrap(cross_section)
    ob_list_before = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for ii in cap_inds:
        cross_section.data.polygons[ii].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.duplicate_move()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob_list_after = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
    new_face_ob = [ob for ob in ob_list_after if ob not in ob_list_before][0]
    new_face_ob.name = "cross-sectional area"
    mat = bpy.data.materials["cross_section_material"]
    new_face_ob.data.materials.append(mat)  # added for 2.79
    new_face_ob.material_slots[0].material = mat
    return(new_face_ob)

###################################################################################




def make_plane_unwrap(centerline, ind, norm_here=[]):
    # Create plane perpendicular to centerline at vertex ind
    # Side length half length of centerline, arbitrary
    # rad = max(2*max_rad, get_dist(centerline.data.vertices[0].co, centerline.data.vertices[-1].co) / 8)
    rad = bpy.context.scene.search_radius

    p0 = centerline.data.vertices[ind].co

    parallel_xsections = bpy.context.scene.parallel_xsections
    if parallel_xsections:
        # Assign same normal to all cross sections
        norm_here = norm_here

    else:
        # Calculate weighted average of two prior and two next normals
        if ind == 0 or ind == 1:
            p_1 = centerline.data.vertices[1].co
            p_0 = centerline.data.vertices[0].co
            norm_m1 = p_1 - p_0
            norm_m2 = norm_m1
        else:
            pm1 = centerline.data.vertices[ind-1].co
            pm2 = centerline.data.vertices[ind-2].co
            norm_m1 = p0 - pm1
            norm_m2 = pm1 - pm2

        N = len(centerline.data.vertices)
        if ind == N-1 or ind == N-2:
            p_N = centerline.data.vertices[N-1].co
            p_Nm1 = centerline.data.vertices[N-2].co
            norm_p1 = p_N - p_Nm1
            norm_p2 = norm_p1
        else:
            pp1 = centerline.data.vertices[ind+1].co
            pp2 = centerline.data.vertices[ind+2].co
            norm_p1 = pp1 - p0
            norm_p2 = pp2 - pp1

        norm_m1 = Vector(norm_m1 / np.linalg.norm(norm_m1))
        norm_m2 = Vector(norm_m2 / np.linalg.norm(norm_m2))
        norm_p1 = Vector(norm_p1 / np.linalg.norm(norm_p1))
        norm_p2 = Vector(norm_p2 / np.linalg.norm(norm_p2))
        norm_here = (norm_m1+norm_p1+norm_m2/2+norm_p2/2) / 3

    # Construct plane, assign normal
    bpy.ops.mesh.primitive_plane_add(location = p0, radius = rad)
    plane = bpy.context.object
    plane.rotation_mode = 'QUATERNION'
    plane.rotation_quaternion = norm_here.to_track_quat('Z','Y')

    return(plane)



def get_yaxis_pt_unwrap(plane, norm, centerline, ctrline_ind, self):
    # Find intersection point of yaxis and plane

    if bpy.context.scene.yaxis_name == "":
        self.report({'INFO'}, "no y-axis selected, deliberate crash")
        x = no_y_axis_selected_deliberate_crash

    yaxis = bpy.data.objects[bpy.context.scene.yaxis_name]

    # Find which edge on yaxis intersects the plane
    no_intersect = True
    eind = 0
    y_edges = yaxis.data.edges
    y_verts = yaxis.data.vertices
    while no_intersect:
        verts_i = list(y_edges[eind].vertices)
        v0_co = y_verts[verts_i[0]].co
        v1_co = y_verts[verts_i[1]].co
        edge_dir = v1_co - v0_co
        edge_len = edge_dir.length
        edge_dir = edge_dir / edge_len
        result, pt_intersect, face_normal, face_idx = plane.ray_cast(v0_co, edge_dir, distance=edge_len)
        if result == True:
            no_intersect = False
            ypt1_ind = verts_i[0]
            ypt2_ind = verts_i[1]
        else:
            eind += 1
            if eind >= len(y_edges):
                print("no intersect found between plane and yaxis, breaking code")
                x = break_code

    # Add vertex at pt_intersect between ypt1_ind and ypt2_ind
    bpy.ops.object.mode_set(mode='OBJECT')
    select_obj_unwrap(yaxis)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.object.data.vertices[ypt1_ind].select = True
    bpy.context.object.data.vertices[ypt2_ind].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide()
    bpy.ops.object.mode_set(mode='OBJECT')
    newind = len(bpy.context.object.data.vertices) - 1  # the newly added point
    bpy.context.object.data.vertices[newind].co = pt_intersect

    return(pt_intersect, newind)




# Project vesicles to axon surface
class ProjectVesicles2Surf_unwrap(bpy.types.Operator):
    """Project vesicles to axon surface (input: centerline)"""
    bl_idname = "object.project_to_surf_unwrap"
    bl_label = "Project vesicles to axon surface"

    def execute(self, context):
        centerline = bpy.context.object
        vesicle_list = centerline["vesicle_list"]

        print("projecting vesicles to surface...")
        proj_vesicles_to_surf_unwrap(centerline, vesicle_list)

        return {'FINISHED'}

# Project synapse object to axon surface
class ProjectSynapse2Surf_unwrap(bpy.types.Operator):
    """Project synapse to axon surface (input: centerline, synapse)"""
    bl_idname = "object.project_syn_to_surf_unwrap"
    bl_label = "Project synapse to axon surface"

    def execute(self, context):
        err, objs = assign_selected_objects_unwrap(self)
        if err < 0:
            return {'FINISHED'}
        centerline, meshobj = objs

        print("projecting synapse to surface...")
        proj_mesh_to_surf_unwrap(centerline, meshobj)

        return {'FINISHED'}



def unwrap_crosssection_boundaries_unwrap(centerline, self):
    # Get the (x,y) coordinates of each crosssection boundary vertex
    # relative to the "y-axis" and distance from y-axis
    # store as new centerline variable

    t1 = datetime.datetime.now()

    # Get endpoint of yaxis_ob (note: vertices not ordered)
    # Count # edges per vertex, as verts with only one connecting edge are endpoints
    yaxis_ob = bpy.data.objects[bpy.context.scene.yaxis_name]
    vert_edge_counts = [0] * len(yaxis_ob.data.vertices)
    for ed in yaxis_ob.data.edges:
        vert_edge_counts[ed.vertices[0]] += 1
        vert_edge_counts[ed.vertices[1]] += 1

    end_inds = [ind for [ind, count] in enumerate(vert_edge_counts) if count == 1]
    yaxis0_ind = end_inds[0]  # no reason to choose one over the other

    norm_vec = get_norm_centerline_unwrap(centerline)

    # Loop over cross sections
    xy_coords = []
    nverts_centerline = len(centerline.data.vertices)
    for yind in range(0, nverts_centerline):
        print(yind, "/", nverts_centerline)

        # Get this cross section
        this_xsec_name = centerline["cross_section_names"][yind]
        xsection = bpy.data.objects[this_xsec_name]  # context.object?
        face = xsection.data.polygons[0]
        this_yaxis_pt = Vector(centerline["yaxis_pts"][yind])  # xyz vector
        this_yaxis_ind = centerline["yaxis_inds"][yind]

        # Define y-value as distance from yaxis_pt[y0_ind] along y-axis to here
        select_shortest_path_unwrap(yaxis_ob, [this_yaxis_ind, yaxis0_ind], self)
        this_y = get_total_length_of_edges_unwrap(yaxis_ob)

        # Find closest 2 verts to yaxis_pt
        # Use distance from yaxis_pt to these pts, ignore polygon edge between them
        vind1 = -1
        vind2 = -1
        dist1 = 1000000
        dist2 = 1000000
        for vind in face.vertices:
            pt = xsection.data.vertices[vind].co
            this_dist = get_dist_unwrap(this_yaxis_pt, pt)
            if this_dist < dist2:
                if this_dist < dist1:
                    vind2 = vind1
                    dist2 = dist1
                    vind1 = vind
                    dist1 = this_dist
                else:
                    vind2 = vind
                    dist2 = this_dist

        # Find distance from all other vertices around polygon to these vertices
        # Assign vertices to closest starting point, thereby defining cutting point on opposite side of polygon
        vlist1 = []  # Vertices closest to pt1
        vlist2 = []  # Vertices closest to pt2
        for vind in face.vertices:
            if vind == vind1:
                this_dist1 = 0
            else:
                select_shortest_path_unwrap(xsection, [vind1, vind], self)
                this_dist1 = get_total_length_of_edges_unwrap(xsection)
            if vind == vind2:
                this_dist2 = 0
            else:
                select_shortest_path_unwrap(xsection, [vind2, vind], self)
                this_dist2 = get_total_length_of_edges_unwrap(xsection)
            if this_dist1 < this_dist2:
                vlist1.append([vind, this_dist1])
            else:
                vlist2.append([vind, this_dist2])
                # vlist1.sort(key=lambda x: x[1])  # Sort by second element (not actually necessary)
                # vlist2.sort(key=lambda x: x[1])
        
        # Determine negative and positive x in relation to normal of cross section
        # Don't test with vind1, has distance 0 for yaxis
        vec_yaxis_to_v2 = np.array(Vector(xsection.data.vertices[vind2].co - this_yaxis_pt))
        vec_to_ctr = np.array(Vector(xsection.data.vertices[vind2].co - centerline.data.vertices[yind].co))
        cross2 = np.cross(vec_yaxis_to_v2, norm_vec)
        dot2 = np.dot(cross2, vec_to_ctr)  # Positive if point in same direction
        if dot2 > 0:
            sgn1 = -1
            sgn2 = 1
        else:
            sgn1 = 1
            sgn2 = -1

        # Add distance to yaxis_pt to each distance value, assign appropriate sign
        vlist1_sgnd = [[ii, sgn1*(vv+dist1)] for [ii,vv] in vlist1]
        vlist2_sgnd = [[ii, sgn2*(vv+dist2)] for [ii,vv] in vlist2]

        # Combine back into single list (not checked)
        vlist = vlist1_sgnd + vlist2_sgnd
        vlist.sort(key=lambda x: x[0])  # Sort by index

        # Now have y-value (this_y) and x values (vlists), save these in a data structure
        # Order of coords corresponds to order of the vertices per cross section
        xy_coords_here = [[x, this_y] for [ind, x] in vlist]
        xy_coords.append(xy_coords_here)

    t2 = datetime.datetime.now()
    print("\nTime to unwrap cross-section boundaries: ", t2-t1)
    
    pickle.dump(xy_coords, open("/home/anne/Desktop/NeuroMorph/xsection_bdries_for_plotting.p", "wb"))
    return(xy_coords)



class SurfProjectionSetup_unwrap(bpy.types.Operator):
    """Setup projection to surface (input centerline)"""
    bl_idname = "object.setup_surf_proj_unwrap"
    bl_label = "Setup projection to surface (input centerline)"

    def execute(self, context):
        centerline = bpy.context.object

        print("unwrapping cross-section boundaries...")
        xy_coords = unwrap_crosssection_boundaries_unwrap(centerline, self)
        centerline["crosssection_xy_coords"] = xy_coords

        # For debugging
        xsection_obj = xsections_to_single_ob_unwrap(centerline)

        return {'FINISHED'}


def setup_kdt_unwrap(nverts, centerline):
    # Loop through all vertices of all cross-sections, add to kdtree

    nverts = nverts + 500  # why is this necessary?

    kdt = mathutils.kdtree.KDTree(nverts)
    index_offset = 0
    for cline_ind in range(0, len(centerline.data.vertices)):
        this_xsec_name = centerline["cross_section_names"][cline_ind]
        xsection = bpy.data.objects[this_xsec_name]
        for ii, vv in enumerate(xsection.data.vertices):
            print(cline_ind, len(centerline.data.vertices), nverts, ii+index_offset)
            kdt.insert(vv.co, ii+index_offset)
        index_offset += len(xsection.data.vertices)
    kdt.balance()
    return(kdt)



def xsections_to_single_ob_unwrap(centerline):
    mesh = bpy.data.meshes.new("xsection mesh")  # add a new mesh
    obj = bpy.data.objects.new("XSection Verts", mesh)  # add a new object using the mesh
    scene = bpy.context.scene
    scene.objects.link(obj)  # put the object into the scene (link)
    scene.objects.active = obj  # set as the active object in the scene
    obj.select = True  # select object
    mesh = bpy.context.object.data
    bm = bmesh.new()

    for cline_ind in range(0, len(centerline.data.vertices)):
        this_xsec_name = centerline["cross_section_names"][cline_ind]
        xsection = bpy.data.objects[this_xsec_name]
        for ii, vv in enumerate(xsection.data.vertices):
            bm.verts.new(vv.co)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)  
    bm.free()  # always do this when finished

    return(obj)



def proj_vesicles_to_surf_unwrap(centerline, vesicle_list):
    # Calculate distance from each vesicle to each cross section boundary vertex,
    # assign vesicle to coords of closest, store distance

    # Set up kdtree containing all cross-section boundary vertices
    # Flatten xy_coords so indices agree with kdtree
    # Find closest cross-section boundary point to each vesicle center
    # Store xy coordinate of point and distance to point

    xy_coords = centerline["crosssection_xy_coords"]

    # Flatten xy_coords to a single set of indices, to match kdtree indices
    xy_coords_flat = [[pt[0], pt[1]] for layer in xy_coords for pt in layer]
    nverts_all = len(xy_coords_flat)
    kdt = setup_kdt_unwrap(nverts_all, centerline)

    # Get distances from vesicles to cross-section vertices via kd-tree
    vscl_to_xsec_coords = []
    ind = 0
    skipped_count = 0
    for vsc_name in vesicle_list:
        ind+=1
        vsc_obj = bpy.context.scene.objects[vsc_name]
        vsc_ctr = calc_center_unwrap(vsc_obj)  # center point of vsc mesh

        # Calculate closest xsection point to center point
        xsection_co, ii, dist = kdt.find(vsc_ctr)

        print(ind, len(vesicle_list), ii)

        ### Hack, related to nverts = nverts + 500  # why is this necessary?
        if ii >= len(xy_coords_flat):
            print("bad! but ignoring... <------------------------------------------------------------------")
            skipped_count += 1
        else:
        ###

            # Save xy-coords of this point and distance
            xy_here = xy_coords_flat[ii]
            vscl_to_xsec_coords.append([xy_here, dist])

    pickle.dump(vscl_to_xsec_coords, open("/home/anne/Desktop/NeuroMorph/vscl_coords_for_plotting.p", "wb"))
    print("WARNING:", str(skipped_count), "vesicles were ignored due to bad indexing")
    return()


def proj_mesh_to_surf_unwrap(centerline, mesh):
    xy_coords = list(centerline["crosssection_xy_coords"])  # populated with bpy id property array

    xsec_vert_ob = bpy.data.objects["XSection Verts"]
    select_obj_unwrap(xsec_vert_ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


    # Flatten xy_coords to a single set of indices, to match kdtree indices
    xy_coords_flat = [[pt[0], pt[1]] for layer in xy_coords for pt in layer]
    nverts_all = len(xy_coords_flat)
    kdt = setup_kdt_unwrap(nverts_all, centerline)

    # Get distances from vesicles to cross-section vertices via kd-tree
    pts_to_xsec_coords = []
    for vert in mesh.data.vertices:
        # Calculate closest xsection point to center point
        xsection_co, ii, dist = kdt.find(vert.co)

        # Select vertices for debugging
        xsec_vert_ob.data.vertices[ii].select = True

        # Save xy-coords of this point and distance
        xy_here = xy_coords_flat[ii]
        pts_to_xsec_coords.append([xy_here, dist])

    pickle.dump(pts_to_xsec_coords, open("/home/anne/Desktop/NeuroMorph/syn_coords_for_plotting.p", "wb"))
    return()



# Convert objects to global coordinates, call this in all functions to be safe
def convert_to_global_coords_unwrap(these_obs = []):
    selected_ob = bpy.context.object
    activate_an_object_unwrap()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    if these_obs == []:
        these_obs = bpy.context.scene.objects
    for ob in these_obs:
        select_obj_unwrap(ob)
        if ob.type == 'MESH' and hasattr(ob, 'data') and ob.location != Vector([0.0,0.0,0.0]):
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    select_obj_unwrap(selected_ob)


# Count number of vesicles that project to each centerline point
class ProjectVesicles_unwrap(bpy.types.Operator):
    """Project centers of distinct spheres (vesicles) of selected mesh object onto selected centerline object (input: 2 objects)"""
    bl_idname = "object.project_vesicles_unwrap"
    bl_label = "Project vesicle spheres onto centerline"

    # directory = bpy.props.StringProperty(subtype="FILE_PATH")
    # filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        # full_filename = define_filename(self, ".csv")

        # Assign centerline and vesicle object from selected objects
        err, objs = assign_selected_objects_unwrap(self)
        if err < 0:
            return {'FINISHED'}
        centerline, vesicle_obj = objs

        # Convert to global coords
        convert_to_global_coords_unwrap()

        # if len(bpy.context.scene.vesicle_list) == 0:
        if len(centerline["vesicle_list"]) == 0:
            print("computing vesicle list...")
            vesicle_list = get_vesicle_list_unwrap(vesicle_obj)
            centerline["vesicle_list"] = vesicle_list
        else:
            print("loading vesicle list...")
            vesicle_list = centerline["vesicle_list"]

        vcounts = proj_vesicles_unwrap(centerline, vesicle_list)
        centerline["vesicle_counts"] = vcounts

        return {'FINISHED'}



def get_vesicle_list_unwrap(vesicle_obj):
    # Separate by loose parts converts vesicle mass to separate spheres, then make list of sphere center points
    
    # Deselect everything but the vesicle object
    activate_an_object_unwrap()
    bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.scene.objects.active = vesicle_obj
    # vesicle_obj.select = True
    select_obj_unwrap(vesicle_obj)
    bpy.ops.object.duplicate()  # operate on copy of obj instead
    vesicle_obj_copy = bpy.context.object
    vesicle_obj_copy.parent = vesicle_obj
    ob_list_before = vesicle_obj.children
    select_obj_unwrap(vesicle_obj_copy)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Separate the object into loose parts, ie separate spheres
    t1 = datetime.datetime.now()
    bpy.ops.mesh.separate(type='LOOSE')  # slow
    t2 = datetime.datetime.now()
    print("\nTime to separate spheres: ", t2-t1)

    ob_list_after = vesicle_obj.children
    vesicle_list = [ob.name for ob in ob_list_after if (ob not in ob_list_before or ob.name == vesicle_obj_copy.name)]

    # vesicle_list = [ob.name for ob in bpy.context.scene.objects if ob.select == True]  # replaces original vesicle_obj
    return (vesicle_list)


# Return centerpoint of object, defined as mean vertex value
def calc_center_unwrap(obj):
    v_sum = Vector([0,0,0])
    for v in obj.data.vertices:
        v_sum += v.co
    ctrpt = v_sum / len(obj.data.vertices)
    return(ctrpt)


# Calculate center point of each vesicle (todo: or closest point on surface?)
# Find closest point on centerline to each vesicle center point
# Tally vesicles per centerline vertex
def proj_vesicles_unwrap(ctrline, vesicle_list):
    nverts = len(ctrline.data.vertices)
    kdt = mathutils.kdtree.KDTree(nverts)
    for ii, vv in enumerate(ctrline.data.vertices):
        kdt.insert(vv.co, ii)
    kdt.balance()

    vcounts = [0] * nverts  # count number vesicles that project to each point
    for vsc_name in vesicle_list:
        vsc_obj = bpy.context.scene.objects[vsc_name]
        vsc_ctr = calc_center_unwrap(vsc_obj)  # center point of vsc mesh

        # calculate closest ctrline point to center point
        ctrline_co, ii, dist = kdt.find(vsc_ctr)
        #print(vsc_name, dist, ii, vcounts[ii])
        vcounts[ii] += 1

    return (vcounts)


def select_obj_unwrap(ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = ob
    ob.select = True  # necessary


def get_dist_unwrap(coord1, coord2):  # distance is monotonic, take square root at end for efficiency
    d = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2)
    return d

# Sometimes this is necessary before changing modes
def activate_an_object_unwrap(ob_0=[]):
    tmp = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide == False][0]
    bpy.context.scene.objects.active = tmp  # required before setting object mode

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    if ob_0 == []:
        ob_0 = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide == False][0]
    bpy.context.scene.objects.active = ob_0
    ob_0.select = True


if __name__ == "__main__":
    register()

def register():
    bpy.utils.register_module(__name__)


    bpy.types.Scene.search_radius = bpy.props.FloatProperty \
    (
        name="Search Radius around Centerline Point",
        description = "Size of planes and local mesh region to include when searching for axon-plane intersection", 
        default=1.0  # the only user-adjustable property
    )

    bpy.types.Scene.parallel_xsections = bpy.props.BoolProperty \
    (
        name = "Parallel Cross Sections",
        description = "If checked, all cross sections will be parallel, based on the average direction of the centerline",
        default = True  # must be true for this tool, no way for user to adjust this
    )

    bpy.types.Scene.yaxis_name = bpy.props.StringProperty \
    (
        name = "y-axis object name", 
        description = "Name of edge object that will serve as the y-axis in the axon surface projection", 
        default = ""  # is set internally
    )


def unregister():

    del bpy.types.Scene.yaxis_name
    del bpy.types.Scene.parallel_xsections
    del bpy.types.Scene.search_radius

    bpy.utils.unregister_module(__name__)

