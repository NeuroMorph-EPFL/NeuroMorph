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
XYFolder = mainFolder + "XY_Zstack_Images" + File.separator;
XZFolder = mainFolder + "XZ_Ystack_Images" + File.separator;
ZYFolder = mainFolder + "ZY_Xstack_Images" + File.separator;

getVoxelSize(xSize, ySize, zSize, unit);

Dialog.create("Voxel Depth");
Dialog.addMessage("Please check if the dimensions are correct");
Dialog.addNumber("Voxel width", xSize);
Dialog.addNumber("Voxel height", ySize);
Dialog.addNumber("Voxel depth", zSize);
Dialog.show();
xSize = Dialog.getNumber();
ySize = Dialog.getNumber();
zSize = Dialog.getNumber();

run("Properties...", "channels=1 frames=1 unit=nm pixel_width="+xSize+" pixel_height="+ySize+" voxel_depth="+zSize+"");


if (File.isDirectory(XYFolder) || File.isDirectory(XZFolder) || File.isDirectory(ZYFolder)) {
	exit("Folder of XY, XZ or ZY images already found, macro aborted.");
}

File.makeDirectory(XYFolder);
File.makeDirectory(XZFolder);
File.makeDirectory(ZYFolder);


selectWindow(originalStack);
run("Reslice [/]...", "output="+zSize+" start=Top"); // Vue du haut (XZ);
rename("XZ_Y_");
run("Image Sequence... ", "format=TIFF save="+XZFolder+"XZ_Y_0000.tif");
run("Close");

selectWindow(originalStack);
run("Reslice [/]...", "output="+zSize+" start=Left rotate"); // Vue de cote (ZY);
rename("ZY_X_");
run("Image Sequence... ", "format=TIFF save="+ZYFolder+"ZY_X_0000.tif");
run("Close");

selectWindow(originalStack);
rename("XY_Z_");
run("Image Sequence... ", "format=TIFF save="+XYFolder+"XY_Z_0000.tif");
run("Close");


call("java.lang.System.gc");

