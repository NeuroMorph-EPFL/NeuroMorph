//    Generate_3D_image_stacks.ijm (C) 2016,  Tom Boissonnet
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with this program.  If not, see http://www.gnu.org/licenses/


originalStack= getTitle();
mainFolder = getDirectory("Choose a directory to save the folders of separated images");
ZFolder = mainFolder + "Z_Stack" + File.separator;
YFolder = mainFolder + "Y_Stack" + File.separator;
XFolder = mainFolder + "X_Stack" + File.separator;

getVoxelSize(xSize, ySize, zSize, unit);

Dialog.create("Voxel Depth");
Dialog.addMessage("Please check if the dimensions are correct");
Dialog.addNumber("Voxel width", xSize);
Dialog.addNumber("Voxel height", ySize);
Dialog.addNumber("Voxel depth", zSize);
Dialog.addCheckbox("Create Z stack", true);
Dialog.show();
xSize = Dialog.getNumber();
ySize = Dialog.getNumber();
zSize = Dialog.getNumber();
createZ = Dialog.getCheckbox();

run("Properties...", "channels=1 frames=1 unit=nm pixel_width="+xSize+" pixel_height="+ySize+" voxel_depth="+zSize+"");


if ((createZ && File.isDirectory(ZFolder)) || File.isDirectory(YFolder) || File.isDirectory(XFolder)) {
	exit("Folder of Z, Y or X stack already found, macro aborted.");
}

if (createZ) {
	File.makeDirectory(ZFolder);
}
File.makeDirectory(YFolder);
File.makeDirectory(XFolder);


selectWindow(originalStack);
run("Reslice [/]...", "output="+zSize+" start=Top"); // Vue du haut (Z);
rename("Y_");
run("Image Sequence... ", "format=TIFF save=["+YFolder+"Y_0000.tif]");
run("Close");

selectWindow(originalStack);
run("Reslice [/]...", "output="+zSize+" start=Left rotate"); // Vue de cote (X);
rename("X_");
run("Image Sequence... ", "format=TIFF save=["+XFolder+"X_0000.tif]");
run("Close");

selectWindow(originalStack);
if (createZ) {
	rename("Z_");
	run("Image Sequence... ", "format=TIFF save=["+ZFolder+"Z_0000.tif]");
}
run("Close");


call("java.lang.System.gc");

