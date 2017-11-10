*These files have been deprecated.  They are provided only for legacy purposes, as they were released with our 2014 Neuroinformatics paper.*

[Legacy Blender Wiki](http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Neuro_tool)  (including installation instructions)


#### NeuroMorph Measurement Tools   ([download](https://raw.githubusercontent.com/NeuroMorph-EPFL/NeuroMorph/master/Legacy_NeuroMorph_Toolkit/NeuroMorph_Measurement_Tools.py))
This module measures surface areas, volumes, and lengths of regions of meshes specified by a user-defined selection of vertices. New objects are created as children of the original mesh object, and the measurements are stored in appropriate property variables of these children objects in the Geometry Properties panel of the Object context (bottom right of the Blender interface, see documentation for details). Objects are named, optionally, according to a naming convention developed for neural structures. Measurements can be exported into a .txt file that can be read by Excel.


#### NeuroMorph Image Stack Interactions   ([download](http://raw.githubusercontent.com/NeuroMorph-EPFL/NeuroMorph/master/Legacy_NeuroMorph_Toolkit/NeuroMorph_Image_Stack_Interactions.py))
This module superimposes images from the original (electron microscopy) image stack onto mesh objects. The images are displayed in the X-Y plane, and are uploaded into empty objects in Blender.  Individual points on the images can be selected, and objects containing those points can be retrieved (from the possibly hundreds or thousands of invisible objects in the scene) and made visible, allowing for easy navigation of object connectivity.  Images can be viewed in all 3 dimensions using the output from the Generate 3D Image Stacks fiji macro provided.

[![Analytics](https://ga-beacon.appspot.com/UA-99596205-1/Legacy_NeuroMorph_Toolkit?pixel)](https://github.com/NeuroMorph-EPFL/NeuroMorph/tree/master/Legacy_NeuroMorph_Toolkit)
