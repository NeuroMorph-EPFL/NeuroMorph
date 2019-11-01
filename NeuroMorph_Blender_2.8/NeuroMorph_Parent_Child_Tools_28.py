#    NeuroMorph_Parent_Child_Tools.py (C) 2019,  Anne Jorstad
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
    "name": "NeuroMorph Parent-Child Tools",
    "author": "Anne Jorstad",
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > NeuroMorph > Parent-Child Tools",
    "description": "Parent-Child Tools",
    "wiki_url": "https://github.com/NeuroMorph-EPFL/NeuroMorph/wiki/Other-Tools#parent-child-tools",   
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
import numpy as np


# Define the panel
class NEUROMORPH_PT_ParentChildPanel(bpy.types.Panel):
    bl_idname = "NEUROMORPH_PT_ParentChildPanel"
    bl_label = "Parent-Child Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeuroMorph"

    def draw(self, context):

        layout = self.layout
        layout.use_property_split = True

        split = layout.split(factor=0.5, align=True)
        col1 = split.column()
        col1.operator("neuromorph.show_children", text="Show Children")
        col2 = split.column()
        col2.operator("neuromorph.hide_children", text="Hide Children")

        split = layout.split(factor=0.5, align=True)
        col1 = split.column()
        col1.operator("neuromorph.select_children", text="Select Children")
        col2 = split.column()
        col2.operator("neuromorph.delete_children", text="Delete Children")

        row = layout.row()
        row.operator_menu_enum("neuromorph.assign_parent", "select_objects", text = "Assign Parent Object")




# Show/Hide children of active object
class NEUROMORPH_OT_show_children(bpy.types.Operator):
    """Show all children of active object"""
    bl_idname = "neuromorph.show_children"
    bl_label = "Show all children of active object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_ob = bpy.context.object
        children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        for ob in children:
            ob.hide_set(False)
        return {'FINISHED'}

class NEUROMORPH_OT_hide_children(bpy.types.Operator):
    """Hide all children of active object"""
    bl_idname = "neuromorph.hide_children"
    bl_label = "Hide all children of active object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_ob = bpy.context.object
        children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        for ob in children:
            ob.hide_set(True)
        return {'FINISHED'}


# Select children of active object
class NEUROMORPH_OT_select_children(bpy.types.Operator):
    """Select all children of active object"""
    bl_idname = "neuromorph.select_children"
    bl_label = "Select all children of active object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_ob = bpy.context.object
        children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        bpy.ops.object.select_all(action='DESELECT')
        for ob in children:
            ob.select_set(True)
        return {'FINISHED'}


# Delete children of active object
class NEUROMORPH_OT_delete_children(bpy.types.Operator):
    """Delete all children of active object (parent must be visible)"""
    bl_idname = "neuromorph.delete_children"
    bl_label = "Delete all children of active object (parent must be visible)"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT') 
        ob = bpy.context.object
        bpy.ops.object.select_all(action='DESELECT')

        for child in ob.children:
            child.hide_set(False)
            child.select_set(True)
            bpy.context.view_layer.objects.active = child
            bpy.ops.object.delete()

        return {'FINISHED'}


# Assign parent object to all selected objects
class NEUROMORPH_OT_assign_parent(bpy.types.Operator):
    '''Assign chosen object as parent to all selected objects'''
    bl_idname = "neuromorph.assign_parent"
    bl_label = "Assign Parent Object"
    bl_options = {"REGISTER", "UNDO"}

    def available_objects(self,context):
        objs_to_ignore = ["Camera", "Lamp", "Light", "Image", "ImageStackLadder"]
        items = [(str(i),x.name,x.name) for i,x in enumerate(bpy.data.objects) if x.parent is None and x.name not in objs_to_ignore]
        return items
    select_objects: bpy.props.EnumProperty(items = available_objects, name = "Available Objects")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self,context):
        active_obs = [ob for ob in bpy.data.objects if ob.select_get() == True]

        # The active object will be the parent of all selected objects
        the_parent = bpy.data.objects[int(self.select_objects)]
        bpy.context.view_layer.objects.active = the_parent
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
        for ob in active_obs:
            ob.parent = the_parent

        return {'FINISHED'}  




classes = (
    NEUROMORPH_PT_ParentChildPanel,
    NEUROMORPH_OT_show_children,
    NEUROMORPH_OT_hide_children,
    NEUROMORPH_OT_select_children,
    NEUROMORPH_OT_delete_children,
    NEUROMORPH_OT_assign_parent
)
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()


