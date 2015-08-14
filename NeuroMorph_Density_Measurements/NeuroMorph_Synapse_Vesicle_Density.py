#    NeuroMorph_Synapse_Density.py (C) 2015,  Anne Jorstad
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
    "name": "NeuroMorph Synapse Vesicle Density",
    "author": "Anne Jorstad",
    "version": (1, 0, 0),
    "blender": (2, 7, 3),
    "location": "View3D > Vesicle to Synapse Distances",
    "description": "Calculate distances from vesicles to a synapse",
    "warning": "",  
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Neuro_tool/visualization",  
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


# Define the panel
class SuperimposePanel(bpy.types.Panel):
    bl_label = "Vesicle to Synapse Distances"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):

        row = self.layout.row()
        row.operator("scene.set_synapse", text='Set Synapse to Highlighted Object')

        row = self.layout.row()
        self.layout.prop(context.scene, 'vesicle_prefix')

        row = self.layout.row()
        row.operator("file.set_vesicle_filename", text='Set File Name and Path for Export', icon='FILESEL')

        row = self.layout.row()
        row.operator("object.get_density", text='Calculate Distances')


class SetSynapse(bpy.types.Operator):
    """Define the synapse to be used for distance calculations (highlight the object, then click here)"""
    bl_idname = "scene.set_synapse"
    bl_label = "Define the synapse to be used"
    
    def execute(self, context):
        bpy.types.Scene.the_synapse = bpy.context.object
        return {'FINISHED'}



class DefineFile(bpy.types.Operator):
    """Define file name and path for distance measurement export."""
    bl_idname = "file.set_vesicle_filename"
    bl_label = "Define file path and name"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        directory = self.directory
        filename = self.filename
        fname = filename + '.csv'
        full_filename = os.path.join(directory, fname)
        bpy.types.Scene.filename = full_filename
        return {'FINISHED'}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def write_density_data(dists, all_vesicles, synapse_name, mean_dist):
    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")
    full_filename = bpy.types.Scene.filename

    f = open(full_filename, 'w')
    f.write('Vesicle Name,Distance to Synapse,' + synapse_name + '\n\n')

    for ind, d in enumerate(dists):
        f.write(all_vesicles[ind].name + "," + str(d) + '\n')

    f.write('\n')
    f.write('mean distance,' + str(mean_dist))
    f.close()



class CalculateVesicleDistances(bpy.types.Operator):
    """Calculate density of all vesicles relative to the synapse (might require all objects to be in the same layer)"""
    # this might only work if all objects are in the same layer
    bl_idname = "object.get_density"
    bl_label = "Calculate distances of all vesicles to the synapse"
    
    def execute(self, context):

        if hasattr(bpy.types.Scene.the_synapse, 'name'):
            the_synapse = bpy.types.Scene.the_synapse
        else:
            self.report({'ERROR'}, 'Synapse not assigned.  First set synapse object.')
            return {'FINISHED'}

        vesicle_prefix = context.scene.vesicle_prefix

        # Extract the synapse and list of all vesicles
        len_vstr = len(vesicle_prefix)
        all_vesicles = []
        for obj in bpy.data.objects:
            this_name = obj.name
            if this_name[0:len_vstr] == vesicle_prefix:
                all_vesicles.append(obj)

        if len(all_vesicles) == 0:
            self.report({'ERROR'}, 'No objects were found with the prefix "' + vesicle_prefix + '".')
            return {'FINISHED'}

        # Calculate center coordinates of each vesicle
        vesicle_centers = []
        mat = all_vesicles[0].matrix_world
        for vscl in all_vesicles:
            these_verts = vscl.data.vertices
            nverts = len(these_verts)
            v_sum = Vector([0,0,0])
            for vert in these_verts:
                these_global_coords = mat * vert.co
                v_sum += these_global_coords
            this_mean = v_sum / nverts
            vesicle_centers.append(this_mean)

        # Calculate distance from each vesicle center to each vertex on synapse
        dists = []
        inds = []
        mat_syn = all_vesicles[0].matrix_world
        for v_ctr in vesicle_centers:
            this_min = sys.maxsize
            this_ind = -1
            for ind, s_vrt in enumerate(the_synapse.data.vertices):
                this_dist = get_dist(v_ctr, mat_syn*s_vrt.co)
                if this_dist < this_min:
                    this_min = this_dist
                    this_ind = ind
            dists.append(this_min)
            inds.append(this_ind)

        mean_dist = sum(dists) / len(dists)
        # mean_3D = [sum(col) / float(len(col)) for col in zip(*dists)]

        # Write file containing all distances and mean
        write_density_data(dists, all_vesicles, the_synapse.name, mean_dist)

        return {'FINISHED'}



def get_dist(coord1, coord2):
    d = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + \
        (coord1[2] - coord2[2])**2)
    return d


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.the_synapse = []
    bpy.types.Scene.vesicle_prefix = StringProperty(name = "Vesicle Prefix", default="vesicle")
    bpy.types.Scene.filename = StringProperty(name = "File name and path", default="/synapse_distances.csv")

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.the_synapse
    del bpy.types.Scene.vesicle_prefix
    del bpy.types.Scene.filename



if __name__ == "__main__":
    register()

