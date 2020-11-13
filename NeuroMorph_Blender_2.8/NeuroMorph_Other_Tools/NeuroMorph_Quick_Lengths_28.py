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
    "name": "NeuroMorph Quick Lengths:  Measure lengths and export",
    "description": "Export lengths measured using the Measure Tool",
    "author": "Anne Jorstad",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > NeuroMorph > Quick Lengths",
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
from bpy_extras.io_utils import ExportHelper, ImportHelper


class NEUROMORPH_PT_QuickLengthPanel(bpy.types.Panel):
    bl_idname = "NEUROMORPH_PT_QuickLengthPanel"
    bl_label = "Quick Lengths"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeuroMorph"

    def draw(self, context):
        layout = self.layout
        layout.operator("neuromorph.export_lengths", text = "Export Lengths")



class NEUROMORPH_OT_export_lengths(bpy.types.Operator, ExportHelper):
    """Export all lengths measured using the Measure Tool"""
    bl_idname = "neuromorph.export_lengths"
    bl_label = "Export lengths"
   
    filename_ext = ".csv"  # ExportHelper mixin class uses this  
    def execute(self, context):
        filepath = self.filepath
        f = open(filepath, 'w')
        f.write('Segment Index,Length,Point 1,Point 2\n')

        lengths, p1s, p2s = get_lengths()
        nsegs = len(lengths)
        print(nsegs)
        for ii in range(0,nsegs):
            f.write(str(ii+1) + "," + str(lengths[ii]) + "," + pt2str(p1s[ii]) + "," + pt2str(p2s[ii]) + "\n")

        f.close()
        return{'FINISHED'}


def get_lengths():
    lengths = []
    p1s = []
    p2s = []
    ruler_data = bpy.data.grease_pencils["Annotations"].layers['RulerData3D']
    frame = ruler_data.frames[0]
    for stroke in frame.strokes:
        p1, p2 = stroke.points[0], stroke.points[-1]
        length = (p1.co - p2.co).length
        lengths.append(length)
        p1s.append(p1)
        p2s.append(p2)
    return lengths, p1s, p2s


def pt2str(point):
    vec = point.co
    vec_str = "[" + str(vec[0]) + ";" + str(vec[1]) + ";" + str(vec[2]) + "]"
    return(vec_str)




classes = (
    NEUROMORPH_PT_QuickLengthPanel,
    NEUROMORPH_OT_export_lengths,
)
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()


