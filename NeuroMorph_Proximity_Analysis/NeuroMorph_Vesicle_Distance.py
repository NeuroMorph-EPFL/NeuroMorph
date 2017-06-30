#    NeuroMorph_Vesicle_Distance.py (C) 2015,  Anne Jorstad
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
    "name": "NeuroMorph Synapse Vesicle Distances",
    "author": "Anne Jorstad",
    "version": (1, 2, 0),
    "blender": (2, 7, 7),
    "location": "View3D > Vesicle to Synapse Distances",
    "description": "Calculate distances from vesicles to a synapse",
    "warning": "",  
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Proximity_Analysis_Tools",  
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


# Define scene variables
bpy.types.Scene.filename = bpy.props.StringProperty \
    (
        name = "Output file", 
        description = "Set file name and path for output data", 
        default = "/"
    )


# Define the panel
class VesicleDistancePanel(bpy.types.Panel):
    bl_label = "Vesicle to Synapse Distances"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "NeuroMorph"

    def draw(self, context):

        row = self.layout.row()
        row.operator("object.reduce_spheres", text='Reduce Spheres to Points')

        row = self.layout.row(align=True)
        row.prop(context.scene, "filename")
        row.operator("file.set_filename", text='', icon='FILESEL')

        row = self.layout.row()
        row.operator("object.get_distances", text='Calculate Distances to Active Object')


# Define file name and path for export
class DefineFile(bpy.types.Operator):
    """Define file name and path for distance measurement export"""
    bl_idname = "file.set_filename"
    bl_label = "Define file path and name"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        directory = self.directory
        filename = self.filename
        fname = filename + '.csv'
        full_filename = os.path.join(directory, fname)
        bpy.context.scene.filename = full_filename
        return {'FINISHED'}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}


# Write distances data to file
def write_distance_data(dists, all_vesicles, synapse_name, mean_dist):
    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")
    full_filename = bpy.context.scene.filename

    f = open(full_filename, 'w')
    f.write('Vesicle Name,Distance to ' + synapse_name + '\n\n')

    for ind, d in enumerate(dists):
        f.write(all_vesicles[ind].name + "," + str(d) + '\n')

    f.write('\n')
    f.write('mean distance,' + str(mean_dist))
    f.close()


# Calculate distance from center of every child object to the active object, and write file
class CalculateVesicleDistances(bpy.types.Operator):
    """Calculate distance of all child vesicles to the active synapse"""
    bl_idname = "object.get_distances"
    bl_label = "Calculate distances of all child vesicles to the selected synapse"
    
    def execute(self, context):

        # Assign objects considered here
        the_synapse = bpy.context.object
        all_vesicles = the_synapse.children

        if all_vesicles == ():
            self.report({'ERROR'}, 'Active object has no children.')
            return {'FINISHED'}

        # Calculate center coordinates of each vesicle
        vesicle_centers = []
        for vscl in all_vesicles:
            mat_vscl = vscl.matrix_world
            these_verts = vscl.data.vertices
            nverts = len(these_verts)
            v_sum = Vector([0,0,0])
            for vert in these_verts:
                these_global_coords = mat_vscl * vert.co
                v_sum += these_global_coords
            this_mean = v_sum / nverts
            vesicle_centers.append(this_mean)

        # Calculate distance from each vesicle center to each vertex on synapse
        dists = []
        inds = []
        mat_syn = the_synapse.matrix_world
        for v_ind, v_ctr in enumerate(vesicle_centers):
            this_min = sys.maxsize
            this_ind = -1
            for s_ind, s_vrt in enumerate(the_synapse.data.vertices):
                this_dist = get_dist_sq(v_ctr, mat_syn*s_vrt.co)
                if this_dist < this_min:
                    this_min = this_dist
                    this_ind = s_ind
                    
            dists.append(math.sqrt(this_min))
            inds.append(this_ind)

        mean_dist = sum(dists) / len(dists)
        # mean_3D = [sum(col) / float(len(col)) for col in zip(*dists)]

        # Write file containing all distances and mean
        write_distance_data(dists, all_vesicles, the_synapse.name, mean_dist)

        return {'FINISHED'}


# Calculate distance from center of every child object to the active object, and write file
class Sphere2Point(bpy.types.Operator):
    """Replace each child mesh of selected object by single point at the object's center (useful when very many objects in scene)"""
    bl_idname = "object.reduce_spheres"
    bl_label = "Replace each child mesh of selected object by single point at the object's center  (useful when very many objects in scene)"
    
    def execute(self, context):
        vscls_as_children = True
        
        # Assumes active object is parent, with many child meshes
        if vscls_as_children:
            parent_ob = bpy.context.object
            vscl_list = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH' \
                                                            and ob_i.parent == parent_ob]
            if len(vscl_list) == 0:
                self.report({'INFO'}, "Selected object has no mesh children.")

            else:
                # Convert to world coordinates
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                parent_ob.select = True
                bpy.context.scene.objects.active = parent_ob
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                for ob in vscl_list:
                    ob.select = True
                    bpy.context.scene.objects.active = ob
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                # Convert to points
                vert_ob_list = spheres2pts(vscl_list)

                # Reassign parent object
                for vert_ob in vert_ob_list:
                    vert_ob.parent = parent_ob


        # # Assumes active object is single object consisting of many joined distinct vescile meshes
        # else:
        #     vscl_ob = bpy.context.object
        #     bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        #     # Store list of already-existing objects
        #     ob_list_before = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']

        #     # Separate into distinct sphere objects
        #     bpy.ops.object.mode_set(mode='EDIT')
        #     bpy.ops.mesh.select_all(action='SELECT')  # edit mode
        #     bpy.ops.object.mode_set(mode='OBJECT')
        #     bpy.ops.mesh.separate(type='LOOSE')     # each discontiguous region is a separate object

        #     # Get list of only new objects = the spheres
        #     ob_list_after = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
        #     for ob_i in ob_list_before:
        #         ob_list_after.remove(ob_i)

        #     ob_list_after.append(vscl_ob)  # is now just one of the spheres

        #     # Replace each sphere with only its centerpoint
        #     vert_ob_list = spheres2pts(ob_list_after)

        #     # Return new vertex objects joined into single object
        #     bpy.ops.object.mode_set(mode='OBJECT')
        #     bpy.ops.object.select_all(action='DESELECT')
        #     for vert_ob in vert_ob_list:
        #         vert_ob.select = True
        #     bpy.context.scene.objects.active = vert_ob_list[0]
        #     bpy.ops.object.join()

        return {'FINISHED'}



# Calculate center of sphere, delete sphere, add new object 
# with single vertex at center of sphere, same name as sphere
def spheres2pts(spherelist):
    vert_ob_list = []
    for vscl in spherelist:
        # Select object and all vertices
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        vscl.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        these_verts = vscl.data.vertices
        nverts = len(these_verts)
        v_sum = Vector([0,0,0])
        for vert in these_verts:
            v_sum += vert.co

        this_mean = v_sum / nverts

        # Delete vscl object
        # To delete selected vertices:  bpy.ops.mesh.delete(type='VERT')
        this_name = vscl.name
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.delete()

        # Create new single vertex object at vscl_mean
        me = bpy.data.meshes.new(this_name)
        vscl_ctr_ob = bpy.data.objects.new(this_name, me)
        bpy.context.scene.objects.link(vscl_ctr_ob)
        me.from_pydata([this_mean], [], [])
        me.update()
        vert_ob_list.append(vscl_ctr_ob)

    # Return an active object
    vert_ob_list[0].select = True
    bpy.context.scene.objects.active = vert_ob_list[0]

    return(vert_ob_list)



def get_dist_sq(coord1, coord2):  # distance is monotonic, take square root at end for efficiency
    d = (coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2
    return d



def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
