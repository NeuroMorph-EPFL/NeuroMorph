#    NeuroMorph_Image_Stack_Interactions.py (C) 2020,  Biagio Nigro, Anne Jorstad, Tom Boissonnet
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
    "name": "NeuroMorph Retrieve Object From Image",
    "author": "Biagio Nigro, Anne Jorstad, Tom Boissonnet",
    "version": (2, 0, 0),
    "blender": (2, 83, 0),
    "location": "View3D > NeuroMorph > Retrieve Object from Image",
    "description": "Retrieve object from point selection on image plane", 
    "wiki_url": "",  
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
import numpy as np



# Define the panel
class NEUROMORPH_PT_RetrieveObjectPanel(bpy.types.Panel):
    bl_idname = "NEUROMORPH_PT_RetrieveObjectPanel"
    bl_label = "Retrieve Object From Image"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeuroMorph"

    def draw(self, context):
        layout = self.layout

        split = layout.row().split(factor=0.33, align=True)
        col1 = split.column()
        col1.operator("neuromorph.display_grid", text="Display Grid")
        col2 = split.column().row()
        col2.prop(context.scene , "x_grid") 
        col2.prop(context.scene , "y_grid") 
        col2.prop(context.scene , "z_grid")
        
        row = layout.row()
        row.operator("neuromorph.pickup_operator", text="Display Object at Selected Vertex")
        
        row = layout.row()
        row.operator("neuromorph.show_names", text="Show Name")
        row.operator("neuromorph.hide_names", text="Hide All Names")



class NEUROMORPH_OT_display_grid(bpy.types.Operator):
    """Display grid on selected image for object point selection"""
    bl_idname = "neuromorph.display_grid"
    bl_label = "Display grid on selected image for object point selection"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
                      
     if bpy.context.mode == 'OBJECT': 
      if bpy.context.active_object is not None:  
             
        if (bpy.context.active_object.name=='Image Z'): 
            mt = bpy.context.active_object
            zlattice=mt.location.z
            x_off=bpy.context.scene.x_side
            y_off=bpy.context.scene.y_side
            xg=bpy.context.scene.x_grid
            yg=bpy.context.scene.y_grid
        elif (bpy.context.active_object.name=='Image X'):
            mt = bpy.context.active_object
            zlattice=mt.location.x
            x_off=bpy.context.scene.z_side
            y_off=bpy.context.scene.y_side
            xg=bpy.context.scene.z_grid
            yg=bpy.context.scene.y_grid
        elif (bpy.context.active_object.name=='Image Y'): 
            mt = bpy.context.active_object
            zlattice=mt.location.y
            x_off=bpy.context.scene.x_side
            y_off=bpy.context.scene.z_side
            xg=bpy.context.scene.x_grid
            yg=bpy.context.scene.z_grid
        else :
            return {"FINISHED"}
 
        tmpActiveObject = bpy.context.active_object
        bpy.ops.object.select_all(action='DESELECT')
        # Delete previous grids
        all_obj = [item.name for item in bpy.data.objects]
        for object_name in all_obj:
          if object_name[0:4]=='Grid':
            delThisObj(bpy.data.objects[object_name])

        bpy.context.view_layer.objects.active = tmpActiveObject
          
        if (bpy.context.active_object.name=='Image Z'): 
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=xg, y_subdivisions=yg, location=(0.0+x_off/2,0.0+y_off/2, zlattice-0.0001))
        elif (bpy.context.active_object.name=='Image X'):
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=xg, y_subdivisions=yg, location=(zlattice-0.0001,0.0+y_off/2, 0.0+x_off/2), rotation=(0,3.141592/2,0)) 
        elif (bpy.context.active_object.name=='Image Y'): 
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=xg, y_subdivisions=yg, location=(0.0+x_off/2, zlattice-0.0001, 0.0+y_off/2), rotation=(3.141592/2,0,0)) 
        
        grid = bpy.context.active_object
        grid.scale.x=x_off/2
        grid.scale.y=y_off/2

        # Delete the faces, so left with only edge grid
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
          
     return {"FINISHED"}


class NEUROMORPH_OT_pickup_operator(bpy.types.Operator):
    """Display mesh objects at all selected grid vertices (will be visible in their respective layers)"""
    bl_idname = "neuromorph.pickup_operator"
    bl_label = "Pick up object Operator"
    bl_options = {"REGISTER", "UNDO"}
    
    # This will only work if all objects are in the same layer
    def execute(self, context):
     if bpy.context.mode == 'EDIT_MESH':   
       if bpy.context.active_object is not None:
         if bpy.context.active_object.name[0:4]=="Grid":
           bpy.ops.object.mode_set(mode = 'OBJECT') 
           grid=bpy.context.active_object 
           selected_idx = [ii.index for ii in grid.data.vertices if ii.select]
           lidx=len(selected_idx)
           l=len(bpy.data.objects)

           if l>0 and lidx>0:  # Loop over all selected vertices
             mindist=float('inf')

             for myob in bpy.data.objects:
               picked_obj_name=""   
               if myob.type=='MESH':
                  if myob.name[0:4]!='Grid':
                    for v_index in selected_idx:
                      # Get local coordinate, turn into word coordinate
                      vert_coordinate = grid.data.vertices[v_index].co  
                      vert_coordinate = grid.matrix_world @ vert_coordinate

                      dist=-1.0
                      if pointInBox(vert_coordinate, myob)==True:
                        dist=findMinDist(vert_coordinate, myob)
                        if dist==0:
                           mindist=dist
                           picked_obj_name=myob.name
                           showObj(picked_obj_name)
                        elif dist>0 and pointInsideMesh(vert_coordinate, myob)==True:
                           mindist=dist
                           picked_obj_name=myob.name
                           showObj(picked_obj_name)

           all_obj = [item.name for item in bpy.data.objects]
           for object_name in all_obj:
             bpy.data.objects[object_name].select_set(False)
             if object_name[0:4]=='Grid':
                delThisObj(bpy.data.objects[object_name])
             
     return {"FINISHED"}


class NEUROMORPH_OT_show_names(bpy.types.Operator):
    """Display name of selected object"""
    bl_idname = "neuromorph.show_names"
    bl_label = "Display name of selected object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # Turn off relationship lines (usually to origin)
        bpy.context.space_data.overlay.show_relationship_lines = False

        if bpy.context.mode == 'OBJECT' and bpy.context.active_object is not None and \
            bpy.context.active_object.type=='MESH':
           
            mt = bpy.context.active_object
            center = centermass(mt)

            # Add empty at the center of the selected object, make it a child, 
            # use this to display name
            bpy.ops.object.add(type='EMPTY', location=center)
            emo = bpy.context.active_object
            emo.parent = mt
            emo.name = mt.name
            emo.show_name = True
            emo.is_name_object = True

        return {'FINISHED'}


class NEUROMORPH_OT_hide_names(bpy.types.Operator):
    """Hide all object names"""
    bl_idname = "neuromorph.hide_names"
    bl_label = "Hide all object names"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        name_obs = [nn for nn in bpy.data.objects if nn.is_name_object == True]
        for nn in name_obs:
            delThisObj(nn)

        return {'FINISHED'}


# Calculate center of mass of a mesh 
def centermass(me):
    sum=mathutils.Vector((0,0,0))
    for v in me.data.vertices:
        sum = sum + v.co
    center = (sum)/len(me.data.vertices)
    return center 

# Control mesh visibility
def showObj(obname):
   if bpy.data.objects[obname].hide_get() == True:
         bpy.data.objects[obname].hide_set(False)
      

# Check if a point falls within bounding box of a mesh
def pointInBox(point, obj):
    
    bound=obj.bound_box
    minx=float('inf')
    miny=float('inf')
    minz=float('inf')
    maxx=-1.0
    maxy=-1.0
    maxz=-1.0
    
    minx=min(bound[0][0], bound[1][0],bound[2][0],bound[3][0],bound[4][0],bound[5][0],bound[6][0],bound[6][0])
    miny=min(bound[0][1], bound[1][1],bound[2][1],bound[3][1],bound[4][1],bound[5][1],bound[6][1],bound[6][1])
    minz=min(bound[0][2], bound[1][2],bound[2][2],bound[3][2],bound[4][2],bound[5][2],bound[6][2],bound[6][2])
    
    maxx=max(bound[0][0], bound[1][0],bound[2][0],bound[3][0],bound[4][0],bound[5][0],bound[6][0],bound[6][0])
    maxy=max(bound[0][1], bound[1][1],bound[2][1],bound[3][1],bound[4][1],bound[5][1],bound[6][1],bound[6][1])
    maxz=max(bound[0][2], bound[1][2],bound[2][2],bound[3][2],bound[4][2],bound[5][2],bound[6][2],bound[6][2])
    
    if (point[0]>minx and point[0]<maxx and point[1]>miny and point[1]<maxy and point[2]>minz and point[2]<maxz):
        return True
    else: 
        return False
    
# Calculate minimum distance among a point in space and mesh vertices    
def findMinDist(point, obj):
    idx = [i.index for i in obj.data.vertices]
    min_dist=float('inf') 
    for v_index in idx:
        vert_coordinate = obj.data.vertices[v_index].co  
        vert_coordinate = obj.matrix_world @ vert_coordinate
        a = (point[0]-vert_coordinate[0])*(point[0]-vert_coordinate[0])
        b = (point[1]-vert_coordinate[1])*(point[1]-vert_coordinate[1])
        c = (point[2]-vert_coordinate[2])*(point[2]-vert_coordinate[2])
        dist=math.sqrt(a+b+c)
        if (dist<min_dist):
            min_dist=dist
    return min_dist


# Check if point is surrounded by ob
# Note: no attempt has been made to handle cases where objects 
#       are in different layers or collections for Blender 2.8x
#       (Blender 2.7x layer code is commented out in place)
def pointInsideMesh(point, ob):
    
    if "surf" in ob.name or "vol" in ob.name or "solid" in ob.name:  # don't display measurement objects
        return False

    # # Copy values of ob.layers
    # layers_ob = []
    # for l in range(len(ob.layers)):
    #     layers_ob.append(ob.layers[l])

    axes = [ mathutils.Vector((1,0,0)), mathutils.Vector((0,1,0)), mathutils.Vector((0,0,1)), mathutils.Vector((-1,0,0)), mathutils.Vector((0,-1,0)), mathutils.Vector((0,0,-1))  ]
    orig=point
    # layers_all = [True for l in range(len(ob.layers))]
    # ob.layers = layers_all  # temporarily assign ob to all layers, for ray_cast()

    this_visibility = ob.hide_get()
    ob.hide_set(False)
    bpy.context.view_layer.update()

    max_dist = 10000.0
    outside = False
    count = 0
    # Send out rays, if cross this object in every direction, point is inside
    for axis in axes:  
        result,location,normal,index = ob.ray_cast(orig,orig+axis*max_dist)  # this will error if ob is in a different layer
        if index != -1:
            count = count+1

    # ob.layers = layers_ob
    ob.hide_set(this_visibility)

    bpy.context.view_layer.update()
    
    if count<6:
        return False
    else: 
    #     # Turn on the layer(s) containing ob in the scene
    #     for l in range(len(bpy.context.scene.layers)):
    #         bpy.context.scene.layers[l] = bpy.context.scene.layers[l] or layers_ob[l]
        return  True
      

# Delete object
def delThisObj(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def ShowBoundingBox(obname):
    bpy.data.objects[obname].show_bounds = True
    return





def register():
    register_classes()

    bpy.types.Scene.x_grid = bpy.props.IntProperty \
          (
            name = "nx",
            description = "Number of grid points in x",
            default = 50,
            min = 1, max = 1000
          )

    bpy.types.Scene.y_grid = bpy.props.IntProperty \
          (
            name = "ny",
            description = "Number of grid points in y",
            default = 50,
            min = 1, max = 1000
          )

    bpy.types.Scene.z_grid = bpy.props.IntProperty \
          (
            name = "nz",
            description = "Number of grid points in z",
            default = 50,
            min = 1, max = 1000
          )

    bpy.types.Object.is_name_object = bpy.props.BoolProperty \
    (
        name = "is name object",
        description = "boolean property noting whether this object is a name object placeholder",
        default = False
    )


def unregister():
    unregister_classes()

    del bpy.types.Scene.x_grid
    del bpy.types.Scene.y_grid
    del bpy.types.Scene.z_grid


classes = (
    NEUROMORPH_PT_RetrieveObjectPanel,
    NEUROMORPH_OT_display_grid,
    NEUROMORPH_OT_pickup_operator,
    NEUROMORPH_OT_show_names,
    NEUROMORPH_OT_hide_names
)
register_classes, unregister_classes = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

