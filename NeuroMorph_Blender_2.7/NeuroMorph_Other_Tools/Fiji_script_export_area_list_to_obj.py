# This Fiji script exports TrakEM2 area lists as Wavefront (.obj) files.


### Please provide the following information:

# Define the sampling resolution.
# Note:  start with ~10, as 1.0 can be very slow.
resample = 3


# Define the location where you would like the files 
# to be exported on your computer.
#    mac format example:     "/Users/username/Desktop/"
#    windows format example: "C:/Users/username/Desktop/"
#    linux format example:   "/home/username/Desktop/"
filepath = "/Users/username/Desktop/"


# Do you want to automatically open the output in Meshlab (mac or linux) or OBJ Viewer (mac only)?
# This software must already be installed on your computer.
#    options: "yes" or "no"
# If so, please provide your operating system
#    options: "mac" or "linux"
open_in_meshlab = "yes"
open_in_OBJ_Viewer = "no"
my_operating_system = "mac"











######################################################################
### Do not change anything below this line.

from ini.trakem2.display import Display
from org.scijava.vecmath import Color3f
from customnode import WavefrontExporter, CustomTriangleMesh
from java.io import StringWriter
from ij.text import TextWindow
from os import system
from io import StringIO
import time


# Function to increment vertex indices so that multiple .obj files
# can be collected in the same file.
# Flip face normals by reversing the order of the last two 
# vertices of each triangle.
def adjust_vertex_indices(meshData, filepath, vert_inc):

	# Save to temporary file, to avoid having the whole file in the buffer
	filename = filepath + "tmp.obj"
	objfile = open(filename, "w")
	objfile.write(meshData.toString())
	objfile.close()
	meshfile = open(filename, "r")

	# Process lines from file
	mesh_str_out = ""
	mesh_inc_str_out = ""
	vertex_count = 0
	for line_ind, line in enumerate(meshfile):
		if line_ind % 10000 == 0 & line_ind > 0:
			print("  processing vertex " + str(line_ind))

		if line[0] == "f":
		# Flip the last two points to flip the normals, 
		# and increment vertex counts 
			line_vec = line.rstrip().split(" ")
			incr = [str(int(elt) + vert_inc) for elt in line_vec[1:4]]
			line_flipped = "f " + line_vec[1] + " " + line_vec[3] + " " + line_vec[2] + "\n"
			line_flipped_and_inc = "f " + incr[0] + " " + incr[2] + " " + incr[1] + "\n"
		else:
		# Don't adjust data; count number of vertices 
			line_flipped = line
			line_flipped_and_inc = line
			if line[0] == "v":
				vertex_count += 1
		mesh_str_out = mesh_str_out + line_flipped
		mesh_inc_str_out = mesh_inc_str_out + line_flipped_and_inc
	return(mesh_str_out, mesh_inc_str_out, vertex_count)


# Create a file to hold collection of all objects together
all_obj_filename = filepath + "all_arealists.obj"
all_mtl_filename = filepath + "all_arealists.mtl"
objfile_all = open(all_obj_filename, "w+")
mtlfile_all = open(all_mtl_filename, "w+")
vertex_increment = 0


# Loop over all area lists
for ii in range(len(Display.getSelected())):
	print("Writing arealist " + str(ii+1))

	arealist = Display.getSelected()[ii]

	# Create the triangle mesh with resample of 1 (no resampling)
	# CAUTION: may take a long time. Try first with a resampling of at least 10.
	# resample = 1
	triangles = arealist.generateTriangles(1, resample)

	# Extract arealist color
	# color = Color3f(1.0, 1.0, 0.0)
	# transparency = 0.0
	red = arealist.color.getRed() / 255.0
	green = arealist.color.getGreen() / 255.0
	blue = arealist.color.getBlue() / 255.0
	this_color = Color3f(red, green, blue)
	this_transparency = arealist.color.getTransparency()

	# Prepare a 3D Viewer object to provide interpretation
	mesh = CustomTriangleMesh(triangles, this_color, this_transparency)
 
	# Save the mesh as Wavefront
	name = "arealist-" + str(arealist).replace(" ", "")  # Remove spaces from name
	m = {name : mesh}
	meshData = StringWriter()
	materialData = StringWriter()
	materialFileName = name + ".mtl"
	objFileName = name + ".obj"
	WavefrontExporter.save(m, materialFileName, meshData, materialData)

	# Flip normals (by defalt they point inward) and 
	# increment vertex indices for file containing all objects together
	t0 = time.time()
	meshData_str, meshData_inc_str, vertex_count = adjust_vertex_indices(meshData, filepath, vertex_increment)
	t1 = time.time()
	print(str(round(t1-t0, 3)) + " seconds")
	
	vertex_increment += vertex_count
	#meshData_str = meshData.toString()
	#meshData_inc_str = meshData.toString()

	# Save .obj file
	full_objfilename = filepath + objFileName
	objfile = open(full_objfilename, "w")
	objfile.write(meshData_str)
	objfile.close()

	# Save .mtl file
	full_mtlfilename = filepath + materialFileName
	mtlfile = open(full_mtlfilename, "w")
	mtlfile.write(materialData.toString())
	mtlfile.close()

	# Append files collecing all objects
	objfile_all.write(meshData_inc_str)
	mtlfile_all.write(materialData.toString())


# Close files
objfile_all.close()
mtlfile_all.close()

print("done writing files!")

# Display the mesh in Meshlab
# note: sys.platform = "java" here, cannot extract OS automatically
if open_in_meshlab == "yes" or open_in_OBJ_Viewer == "yes":
	if my_operating_system == "mac":
		if open_in_meshlab == "yes":
			systemcall_str = "open '" + all_obj_filename + "' -a meshlab"
		if open_in_OBJ_Viewer == "yes":
			systemcall_str = "open '" + all_obj_filename + "' -a OBJ\ Viewer"
		system(systemcall_str)
	elif my_operating_system == "linux":
		systemcall_str = "meshlab '" + all_obj_filename + "'&"
		system(systemcall_str)
	elif my_operating_system == "windows":
		systemcall_str = 'start meshlab "' + all_obj_filename + '"'
		system(systemcall_str)  # Won't work until Fiji updates to jython 2.7.2 (?)

