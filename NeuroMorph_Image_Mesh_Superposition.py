#    NeuroMorph_Image_Mesh_Superposition.py (C) 2014,  Biagio Nigro, Anne Jorstad
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
    "name": "Object-Image superposition",
    "author": "Biagio Nigro, Anne Jorstad",
    "version": (1, 1, 0),
    "blender": (2, 7, 0),
    "location": "View3D > Obj Image superposition",  
    "description": "Superimposes image files over 3D objects interactively",
    "warning": "",  
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Neuro_tool/visualization",  
    "tracker_url": "",  
    "category": "Tool"}  
  
import bpy  
from mathutils import Vector  
import mathutils
import math
import os
import sys

# Define properties
bpy.types.Scene.x_side = bpy.props.FloatProperty \
      (
        name = "x",
        description = "x-dimension of image stack (microns)",
        default = 1
      )
bpy.types.Scene.y_side = bpy.props.FloatProperty \
      (
        name = "y",
        description = "y-dimension of image stack (microns)",
        default = 1
      )
bpy.types.Scene.z_side = bpy.props.FloatProperty \
      (
        name = "z",
        description = "z-dimension of image stack (microns)",
        default = 1
      )

bpy.types.Scene.image_ext = bpy.props.StringProperty \
      (
        name = "ext",
        description = "Image Extension",
        default = ".tif"
      )
      
bpy.types.Scene.image_path = bpy.props.StringProperty \
      (
        name = "Source",
        description = "Location of images in stack (folder must contain no other files)",
        default = "/"
      )
      
bpy.types.Scene.x_grid = bpy.props.IntProperty \
      (
        name = "nx",
        description = "Number of grid points in x",
        default = 50
      )
      
bpy.types.Scene.y_grid = bpy.props.IntProperty \
      (
        name = "ny",
        description = "Number of grid points in y",
        default = 50
      )

bpy.types.Scene.file_min = bpy.props.IntProperty \
      (
        name = "file_min",
        description = "min file number",
        default = 0
      )
      

# Define the panel
class SuperimposePanel(bpy.types.Panel):
    bl_label = "Image Stack Interactions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

 
    def draw(self, context):
        self.layout.label("--Display Images from Stack--")
        self.layout.label("Image Stack Dimensions (microns):")
        row = self.layout.row()
        row.prop(context.scene , "x_side")
        row.prop(context.scene , "y_side")
        row.prop(context.scene , "z_side")
        
        row = self.layout.row(align=True)
        row.prop(context.scene, "image_path")
        row.operator("importfolder.tif", text='', icon='FILESEL')
        
        row = self.layout.row()
        row.operator("superimpose.tif", text='Show Image at Vertex')
        row = self.layout.row()
        row.operator("object.modal_operator", text='Scroll Through Image Stack')
        
        self.layout.label("--Retrieve Object from Image--")
        
        row = self.layout.row()
        row.operator("object.point_operator", text='Display Grid')
        row.prop(context.scene , "x_grid") 
        row.prop(context.scene , "y_grid") 
        
        row = self.layout.row()
        row.operator("object.pickup_operator", text='Display Object at Selected Vertex')
        
        row = self.layout.row()
        row.operator("object.show_names", text='Show Names')
        row.operator("object.hide_names", text='Hide Names')
        
        self.layout.label("--Mesh Transparency--") 
        row = self.layout.row()
        row.operator("object.add_transparency", text='Add Transparency')
        row.operator("object.rem_transparency", text='Remove Transpanrency')
        row = self.layout.row()
        if bpy.context.object is not None:
          mat=bpy.context.object.active_material
          if mat is not None:
             row.prop(mat, "alpha", slider=True)
             row.prop(mat, "diffuse_color", text="")
          
       

def active_node_mat(mat):
    # TODO, 2.4x has a pipeline section, for 2.5 we need to communicate
    # which settings from node-materials are used
    if mat is not None:
        mat_node = mat.active_node_material
        if mat_node:
            return mat_node
        else:
            return mat

    return None               
        

class AddTranspButton(bpy.types.Operator):
    """Define transparency of selected mesh object"""
    bl_idname = "object.add_transparency"
    bl_label = "Add Transparency"
    
    def execute(self, context):
      if bpy.context.mode == 'OBJECT':  
       if (bpy.context.active_object is not None and  bpy.context.active_object.type=='MESH'):
           myob = bpy.context.active_object 
           myob.show_transparent=True
           bpy.data.materials[:]
           if bpy.context.object.active_material:
             matact=bpy.context.object.active_material
             matact.use_transparency=True
             matact.transparency_method = 'Z_TRANSPARENCY'   
             matact.alpha = 0.5
             #matact.diffuse_color = (0.8,0.8,0.8)  
           else: 
             matname=""
             for mater in bpy.data.materials[:]:         
                if mater.name=="_mat_"+myob.name:
                   matname=mater.name
                   break
             if matname=="":   
                mat = bpy.data.materials.new("_mat_"+myob.name)
             else:
                mat=bpy.data.materials[matname]
             mat.use_transparency=True
             mat.transparency_method = 'Z_TRANSPARENCY'            
             mat.alpha = 0.5   
             mat.diffuse_color = (0.8,0.8,0.8)         
             context.object.active_material = mat
             
      return {'FINISHED'} 

class RemTranspButton(bpy.types.Operator):
    """Remove transparency of selected mesh object"""
    bl_idname = "object.rem_transparency"
    bl_label = "Remove Transparency"
    
    def execute(self, context):
      if bpy.context.mode == 'OBJECT':  
       if (bpy.context.active_object is not None and bpy.context.active_object.type=='MESH'):
           myob = bpy.context.active_object 
           if bpy.context.object.active_material:
               matact=bpy.context.object.active_material
               if matact.name[0:5]=="_mat_":
                  
                  matact.use_transparency=False
                  bpy.ops.object.material_slot_remove()
                  bpy.data.materials[:].remove(matact)
                  myob.show_transparent=False
               else:
                  matact.alpha = 1       
                  matact.use_transparency=False
                  myob.show_transparent=False
                  
      return {'FINISHED'} 


class DisplayImageButton(bpy.types.Operator):
    """Display image plane at selected vertex"""
    bl_idname = "superimpose.tif"
    bl_label = "Superimpose image"
    
    
    def execute(self, context):
      if bpy.context.mode == 'EDIT_MESH':
      
        #directory = bpy.props.StringProperty(subtype="FILE_PATH")
        directory = bpy.context.scene.image_path
        #exte = bpy.props.StringProperty(subtype="NONE")
        exte = bpy.context.scene.image_ext
        if os.path.exists(directory):
            
          files = os.listdir(directory)
          N=countFiles(directory, exte)
          if N>2:
            x=bpy.context.scene.x_side
            y=bpy.context.scene.y_side
            z=bpy.context.scene.z_side
            
            if (bpy.context.active_object.type=='MESH'):
                 DisplayImageFunction(directory,exte,files, x,y,z, N)
          else:
            self.report({'INFO'},"No image stack within the selected directory")
        else: 
           self.report({'INFO'},"No image stack directory provided")
      return {'FINISHED'} 
  

class SelectStackFolder(bpy.types.Operator):
    """Select location of images in stack (folder must contain no other files)"""
    bl_idname = "importfolder.tif"
    bl_label = "Select folder of image stack"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.context.scene.image_path = self.directory

        # extract image file extension
        files = os.listdir( self.directory )
        file_ext = os.path.splitext(files[0])[1]
        bpy.context.scene.image_ext = file_ext
        return {'FINISHED'}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        self.exte = bpy.context.scene.image_ext
        return {"RUNNING_MODAL"}


class ModalOperator(bpy.types.Operator):
    """Scroll through image stack from selected image with mouse scroll wheel"""
    bl_idname = "object.modal_operator"
    bl_label = "Simple Modal Operator"

    def __init__(self):
        #print("Start")
        tmpvar=0  # needs something here to compile

    def __del__(self):
        #print("End")
        tmpvar=0  # needs something here to compile

    def modal(self, context, event):
     
     if bpy.context.mode == 'OBJECT':  
       if (bpy.context.active_object.type=='EMPTY'):
        myob = bpy.context.active_object  
        directory = bpy.props.StringProperty(subtype="FILE_PATH")
        directory=bpy.context.scene.image_path
        #exte = bpy.props.StringProperty(subtype="NONE")
        exte = bpy.context.scene.image_ext
        
        files = os.listdir(directory)
        N=countFiles(directory, exte)
        z_max=bpy.context.scene.z_side
        z_min=0
        l=(z_max-z_min)/(N-1)
        bu = [];
        for i in range(0,N):
          bu.append(i*l);
        
        point=myob.location.z
        minim=float('inf')
        i=0
        ind=0
        while i < len(bu):
       
         if abs(bu[i]-point) < minim:
            minim=abs(bu[i]-point)
            ind=i
         else: 
            pass
         i=i+1           
       
        #ind=ind+1
        
        files = os.listdir( directory )
        f=""
        for fi in files:
          if fi[-7:] == '{:03}'.format(ind+bpy.context.scene.file_min)+exte:
            f=fi
          else:
            pass   
            
        if event.type == 'WHEELDOWNMOUSE':  # Apply
           ind=ind-1
           if ind >=0:
             newf=f[0:-7]+'{:03}'.format(ind+bpy.context.scene.file_min)+exte
             
             bpy.data.images.load(directory+newf)
             myob.data = bpy.data.images[newf]
             myob.location.z= myob.location.z-l
            
        if event.type == 'WHEELUPMOUSE':  # Apply
           ind=ind+1
           if ind<=N-1:
             newf=f[0:-7]+'{:03}'.format(ind+bpy.context.scene.file_min)+exte
             
             bpy.data.images.load(directory+newf)
             myob.data = bpy.data.images[newf]
             myob.location.z= myob.location.z+l
            
        elif event.type == 'LEFTMOUSE':  # Confirm
            return {'FINISHED'}
        elif event.type in ('RIGHTMOUSE', 'ESC'):  # Cancel
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if bpy.ops.object.mode_set.poll():
          bpy.ops.object.mode_set(mode='OBJECT')
          if (bpy.context.active_object.type=='EMPTY'):
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
          else:
             return {'FINISHED'}
         

class PointOperator(bpy.types.Operator):
    """Display grid for object point selection"""
    bl_idname = "object.point_operator"
    bl_label = "Choose Point Operator"
    
    def execute(self, context):
                      
     if bpy.context.mode == 'OBJECT': 
      if bpy.context.active_object is not None:  
             
       if (bpy.context.active_object.type=='EMPTY'):    
          mt = bpy.context.active_object
         
          #delete previous grids
          all_obj = [item.name for item in bpy.data.objects]
          for object_name in all_obj:
            bpy.data.objects[object_name].select = False  
            if object_name[0:4]=='Grid':
              delThisObj(bpy.data.objects[object_name]) 
           
          zlattice=mt.location.z
          x_off=bpy.context.scene.x_side
          y_off=bpy.context.scene.y_side
          
          xg=bpy.context.scene.x_grid
          yg=bpy.context.scene.y_grid
       
          bpy.ops.mesh.primitive_grid_add(x_subdivisions=xg, y_subdivisions=yg, location=(0.0+x_off/2,0.0+y_off/2, zlattice-0.0001))
          grid = bpy.context.active_object
          grid.scale.x=x_off/2
          grid.scale.y=y_off/2
          grid.draw_type = 'WIRE'  # don't display opaque grey on the reverse side

          bpy.ops.object.mode_set(mode = 'EDIT')
          bpy.ops.mesh.select_all(action='DESELECT')
          
     return {"FINISHED"}


class PickupOperator(bpy.types.Operator):
    """Display mesh objects at all selected grid vertices (will be visible in their respective layers)"""
    # this will only work if all objects are in the same layer
    bl_idname = "object.pickup_operator"
    bl_label = "Pick up object Operator"
    
    def execute(self, context):
     if bpy.context.mode == 'EDIT_MESH':   
       if bpy.context.active_object is not None:
         if bpy.context.active_object.name[0:4]=="Grid":
           bpy.ops.object.mode_set(mode = 'OBJECT') 
           grid=bpy.context.active_object 
           selected_idx = [i.index for i in grid.data.vertices if i.select]
           lidx=len(selected_idx)
           l=len(bpy.data.objects)

           if l>0 and lidx>0:  # loop over all selected vertices
             mindist=float('inf')

             for myob in bpy.data.objects:
               picked_obj_name=""   
               if myob.type=='MESH':
                  if myob.name[0:4]!='Grid':
                    for v_index in selected_idx:
                      #get local coordinate, turn into word coordinate
                      vert_coordinate = grid.data.vertices[v_index].co  
                      vert_coordinate = grid.matrix_world * vert_coordinate

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
             bpy.data.objects[object_name].select = False  
             if object_name[0:4]=='Grid':
                delThisObj(bpy.data.objects[object_name]) 
             
     return {"FINISHED"}

class ShowNameButton(bpy.types.Operator):
    """Display names of selected objects in the scene"""
    bl_idname = "object.show_names"
    bl_label = "Show Object names"

    def execute(self, context):

        # If show_relationship_lines is not set to false, a blue line
        # from the location of the name object to the origin appears.
        # This line exists between every child object and parent object,
        # but most objects in scene have "location" of (0,0,0).
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].show_relationship_lines = False  # hide parent-child relationship line

        if bpy.context.mode == 'OBJECT': 
         if bpy.context.active_object is not None:      
          if (bpy.context.active_object.type=='MESH'):    
           
            mt = bpy.context.active_object
            child=mt.children
            center=centermass(mt)

            #add empty and make it child
            bpy.ops.object.add(type='EMPTY', location=center)
            emo = bpy.context.active_object
            emo.parent = mt
            #bpy.ops.object.constraint_add(type='CHILD_OF')  # for versions of Blender <= 2.66
            #emo.constraints['Child Of'].target = mt
            #bpy.ops.constraint.childof_set_inverse(constraint=emo.constraints['Child Of'].name, owner='OBJECT')
            emo.name=mt.name+" "
            emo.show_name=True
            emo.empty_draw_size = emo.empty_draw_size / 100

            mt.select=False
            emo.select=False
            stringtmp=""
           
            for obch in child:
               obch.select=True
               bpy.context.scene.objects.active = obch
               if (obch.type=='MESH'):
                  ind=obch.name.find("_")
                  if ind!=-1:
                    stringname=obch.name[0:ind]
                    if (stringname!=stringtmp):

                       center=centermass(obch)
                       bpy.ops.object.add(type='EMPTY', location=center)
                       em = bpy.context.active_object
                       em.parent = mt
                       #bpy.ops.object.constraint_add(type='CHILD_OF')  # for versions of Blender <= 2.66
                       #em.constraints['Child Of'].target = mt
                       #bpy.ops.constraint.childof_set_inverse(constraint=em.constraints['Child Of'].name, owner='OBJECT')
                       em.name=stringname+" "
                       em.show_name=True
                       em.empty_draw_size = emo.empty_draw_size / 100
                       obch.select=False
                       emo.select=False
                       stringtmp=stringname

        return {'FINISHED'}

class HideNameButton(bpy.types.Operator):
    """Hide names of selected objects in the scene"""
    bl_idname = "object.hide_names"
    bl_label = "Hide Object names"
 
   
    def execute(self, context):
        if bpy.context.mode == 'OBJECT': 
         if bpy.context.active_object is not None:  
          mt = bpy.context.active_object    
          if (mt.type=='MESH'):    
           
           child=mt.children
                      
           mt.select=False
                     
           for obch in child:
               if (obch.type=='EMPTY'): 
                 obch.select = True
                 bpy.context.scene.objects.active = obch
        
                 bpy.ops.object.delete() 
        return {'FINISHED'}

#calculate center of mass of a mesh 
def centermass(me):
  sum=mathutils.Vector((0,0,0))
  for v in me.data.vertices:
    sum =sum+ v.co
  center = (sum)/len(me.data.vertices)
  return center 

#control mesh visibility
def showObj(obname):
   if bpy.data.objects[obname].hide == True:
         bpy.data.objects[obname].hide = False
      

#check if a point falls within bounding box of a mesh
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
    
# calculate minimum distance among a point in space and mesh vertices    
def findMinDist(point, obj):
    idx = [i.index for i in obj.data.vertices]
    min_dist=float('inf') 
    for v_index in idx:
       vert_coordinate = obj.data.vertices[v_index].co  
       vert_coordinate = obj.matrix_world * vert_coordinate
       a=(point[0]-vert_coordinate[0])*(point[0]-vert_coordinate[0])
       b=(point[1]-vert_coordinate[1])*(point[1]-vert_coordinate[1])
       c=(point[2]-vert_coordinate[2])*(point[2]-vert_coordinate[2])
       dist=math.sqrt(a+b+c)
       if (dist<min_dist):
            min_dist=dist
    return min_dist


# check if  point is surrounded by a mesh
def pointInsideMesh(point,ob):
    
    if "surf" in ob.name or "vol" in ob.name or "solid" in ob.name:  # don't display measurement objects
        return False

    # copy values of ob.layers
    layers_ob = []
    for l in range(len(ob.layers)):
        layers_ob.append(ob.layers[l])

    axes = [ mathutils.Vector((1,0,0)), mathutils.Vector((0,1,0)), mathutils.Vector((0,0,1)), mathutils.Vector((-1,0,0)), mathutils.Vector((0,-1,0)), mathutils.Vector((0,0,-1))  ]
    orig=point
    layers_all = [True for l in range(len(ob.layers))]
    ob.layers = layers_all  # temporarily assign ob to all layers, for ray_cast()

    this_visibility = ob.hide
    ob.hide = False
    bpy.context.scene.update()

    max_dist = 10000.0
    outside = False
    count = 0
    for axis in axes:  # send out rays, if cross this object in every direction, point is inside
        location,normal,index = ob.ray_cast(orig,orig+axis*max_dist)  # this will error if ob is in a different layer
        if index != -1:
            count = count+1

    ob.layers = layers_ob
    ob.hide = this_visibility

    bpy.context.scene.update()

    if count<6:
        return False
    else: 
        # turn on the layer(s) containing ob in the scene
        for l in range(len(bpy.context.scene.layers)):
            bpy.context.scene.layers[l] = bpy.context.scene.layers[l] or layers_ob[l]

        return  True
      


# delete object
def delThisObj(obj):
    bpy.data.objects[obj.name].select = True
    #bpy.ops.object.select_name(name=obj.name)
    bpy.context.scene.objects.active = obj
    bpy.ops.object.delete() 


def ShowBoundingBox(obname):
    bpy.data.objects[obname].show_bounds = True
    return

#count numeber of files within a folder          
def countFiles(path, exte):
  count=0
  minim=sys.maxsize
  dirs = os.listdir( path )
  for item in dirs:
    if os.path.isfile(os.path.join(path, item)):
       if item[-4:] == exte:
         count = count+1
         
         if int(item[-7:-4]) < minim:
           minim=int(item[-7:-4])    
  bpy.context.scene.file_min=minim   
  
  return count
  
  
#create an empty an empty and upload an image according to the vertical height field (z-axis)
def DisplayImageFunction(directory, exte, files, xx, yy, zz, Nfiles):
 
   myob = bpy.context.active_object  
   bpy.ops.object.mode_set(mode = 'OBJECT')  

   all_obj = [item.name for item in bpy.data.objects]
   for object_name in all_obj:
      bpy.data.objects[object_name].select = False
  
   candidate_list = [item.name for item in bpy.data.objects if item.type == "EMPTY"]

   for object_name in candidate_list:
      bpy.data.objects[object_name].select = True
 
   # remove all selected.
   bpy.ops.object.delete()
  
   x_min=0.0
   x_max=xx
   y_min=0.0
   y_max=yy
   z_min=0.0
   z_max=zz
   
   N=Nfiles

   l=(z_max-z_min)/(N-1)

   bu = [];
   for i in range(0,N):
      bu.append(i*l);
      
   # collect selected verts
   selected_idx = [i.index for i in myob.data.vertices if i.select]
   original_object = myob.name
 
   for v_index in selected_idx:
      # get local coordinate, turn into word coordinate
      vert_coordinate = myob.data.vertices[v_index].co  
      vert_coordinate = myob.matrix_world * vert_coordinate
      
      # unselect all  
      for item in bpy.context.selectable_objects:  
          item.select = False  
       
      # this deals with adding the empty      
      bpy.ops.object.empty_add(type='IMAGE', location=vert_coordinate, rotation=(3.141592653,0,0))  
      mt = bpy.context.active_object 
      mt.name = "Image"
      
      point=vert_coordinate[2]
      minim=float('inf')

      i=0
      ind=0
      while i < len(bu):
       
        if abs(bu[i]-point) < minim:
           minim=abs(bu[i]-point)
           ind=i
        else: 
           pass
        i=i+1           
      
      
      files = os.listdir( directory )
      
      f=""
      
      for fi in files:
        if fi[-7:] == '{:03}'.format(ind+bpy.context.scene.file_min)+exte:
            
            f=fi
        else:
            pass   
            
      bpy.data.images.load(directory+f)
      mt.data = bpy.data.images[f]
      
      mt.scale.x=xx
      mt.scale.y=xx
      mt.location = (0,0+yy, bu[ind])
      
      bpy.ops.object.select_all(action='TOGGLE')  
      bpy.ops.object.select_all(action='DESELECT')  
    
  # set original object to active, selects it, place back into editmode
   bpy.context.scene.objects.active = myob
   myob.select = True  
   bpy.ops.object.mode_set(mode = 'OBJECT')



def register():
    bpy.utils.register_module(__name__)
    
    km = bpy.context.window_manager.keyconfigs.active.keymaps['3D View']
    kmi = km.keymap_items.new(ModalOperator.bl_idname, 'Y', 'PRESS', ctrl=True)
    pass
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
    pass
    
if __name__ == "__main__":
    register()  


