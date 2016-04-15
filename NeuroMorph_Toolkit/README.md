#### NeuroMorph Import Objects   ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Toolkit/NeuroMorph_Import_Objects.py))
This module is used to import one or many object models from .obj files obtained through 3D image segmentation software (e.g. [ilastik](www.ilastik.org) or [TrakEM2](www.ini.uzh.ch/~acardona/trakem2.html)) into Blender, for use with the other NeuroMorph tools.


#### NeuroMorph Measurement Tools   ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Toolkit/NeuroMorph_Measurement_Tools.py))
This module measures surface areas, volumes, and lengths of regions of meshes specified by a user-defined selection of vertices. New objects are created as children of the original mesh object, and the measurements are stored in appropriate property variables of these children objects in the Geometry Properties panel of the Object context (bottom right of the Blender interface, see documentation for details). Objects are named, optionally, according to a naming convention developed for neural structures. Measurements can be exported into a .txt file that can be read by Excel.


#### NeuroMorph Image Stack Interactions   ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Toolkit/NeuroMorph_Image_Stack_Interactions.py))
This module superimposes images from the original (electron microscopy) image stack onto mesh objects. The images are displayed in the X-Y plane, and are uploaded into empty objects in Blender.  Individual points on the images can be selected, and objects containing those points can be retrieved (from the possibly hundreds or thousands of invisible objects in the scene) and made visible, allowing for easy navigation of object connectivity.  Images can be viewed in all 3 dimensions using the output from the Generate 3D Image Stacks fiji macro provided.


#### Generate 3D Image Stacks  ([download](http://raw.githubusercontent.com/ajorstad/NeuroMorph/master/NeuroMorph_Toolkit/Generate_3D_image_stacks.ijm))
This macro for [Fiji](http://fiji.sc/) creates image stacks in the X and Y dimensions, given an image stack in Z.  For use with the NeuroMorph Image Stack Interactions Blender add-on.  Open the original image stack in Fiji (File - Import - Image Sequence), open the .ijm macro file in Fiji, click "Run", choose the location of the new image stack folders, and confirm the voxel dimensions from the original imaging procedure (for our sample EM stack, this is 5, 5, 7.4 um).

