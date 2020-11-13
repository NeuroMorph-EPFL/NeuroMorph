#    NeuroMorph_Quick_Lengths.py (C) 2019,  Anne Jorstad
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
    "name": "NeuroMorph Object List",
    "description": "Export all objects in scene with counts of each types of their children",
    "author": "Anne Jorstad",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > NeuroMorph > Object List",
    "wiki_url": "",
    "category": "Tool"}


import bpy
from bpy.props import *
import math
import mathutils
import os
import re
from os.path import expanduser
import bmesh
from collections import Counter
from bpy_extras.io_utils import ExportHelper, ImportHelper


class NEUROMORPH_PT_ObjectListPanel(bpy.types.Panel):
    bl_idname = "NEUROMORPH_PT_ObjectListPanel"
    bl_label = "Object List"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeuroMorph"

    def draw(self, context):
        layout = self.layout
        layout.operator("neuromorph.export_object_list", text = "Export Object List")



class NEUROMORPH_OT_export_object_list(bpy.types.Operator, ExportHelper):
    """Export all objects in scene with counts of each types of their children"""
    bl_idname = "neuromorph.export_object_list"
    bl_label = "Export object list"
   
    filename_ext = ".csv"  # ExportHelper mixin class uses this  
    def execute(self, context):

        # Extract all unique strings in children object names that appear before numbers.
        # Remove any children with name comaining "_surf", as this is a duplicate with "solid"
        # Assuming solids are maybe more likely that surfs, if one exists without the other.
        # Also remove "_dist" measurement objects.
        all_child_names = [ob.name for ob in bpy.context.scene.objects if ob.parent is not None \
                                                                       and "_surf" not in ob.name \
                                                                       and "_dist" not in ob.name]
        all_child_types = [extract_leading_text(this_name) for this_name in all_child_names]
        types = list(set(all_child_types))
        ntypes = len(types)

        # Setup output file
        filepath = self.filepath
        f = open(filepath, 'w')
        f.write("Parent Name,")
        for ii, tt in enumerate(types):
            f.write(tt)
            if ii != ntypes-1:
                f.write(",")
            else:
                f.write("\n")

        # Get distribution of child types for each parent objects
        parents = [ob for ob in bpy.context.scene.objects if ob.parent is None]
        for pob in parents:
            children = [ob for ob in bpy.context.scene.objects if ob.parent is pob]
            children_types = [extract_leading_text(ch.name) for ch in children]
            counter_counts = Counter(children_types)
            f.write(pob.name + ",")
            for ii, tt in enumerate(types):  # passes over "surf" and "_dist" children
                f.write(str(counter_counts[tt]))
                if ii != ntypes-1:
                    f.write(",")
                else:
                    f.write("\n")
        f.close()
        return{'FINISHED'}


def extract_leading_text(fullname):
    # This function removes the first set of digits from the right
    # leaving in place any numbers that are in the middle of a name
    head = fullname.rstrip('.0123456789')
    return(head)


classes = (
    NEUROMORPH_PT_ObjectListPanel,
    NEUROMORPH_OT_export_object_list,
)
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()


