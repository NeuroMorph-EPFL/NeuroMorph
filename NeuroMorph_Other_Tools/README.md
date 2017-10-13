#### Generate 3D Image Stacks  
[Download](http://raw.githubusercontent.com/ajorstad/NeuroMorph/master/NeuroMorph_Other_Tools/Generate_3D_image_stacks.ijm)  
[Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Other_Tools)  

Macro for [Fiji](http://fiji.sc/) creates image stacks in the X and Y dimensions, given an image stack in Z.  Open the original image stack in Fiji (File - Import - Image Sequence), open the .ijm macro file in Fiji, click "Run", choose the location of the new image stack folders, and confirm the voxel dimensions from the original imaging procedure (for the provided sample EM stack, this is [5, 5, 7.4] nm).  Developed for use with the NeuroMorph Image Stack Interactions Blender add-on.  
(Macro courtesy of Tom Boissonnet.)  
<br>

#### NeuroMorph Parent-Child Tools   
[Download](http://raw.githubusercontent.com/ajorstad/NeuroMorph/master/NeuroMorph_Other_Tools/NeuroMorph_Parent_Child_Tools.py)  
[Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Other_Tools)  

Allows the user to easily to show/hide all children of an object, delete all children of an object, and assign the parent of all selected objects.  
<br>

#### NeuroMorph Import Objects   
[Download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Other_Tools/NeuroMorph_Import_Objects.py)  
[Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Neuro_tool/import)  

Import one or many object models from .obj files obtained through 3D image segmentation software (e.g. [ilastik](www.ilastik.org) or [TrakEM2](www.ini.uzh.ch/~acardona/trakem2.html)) into Blender.  
<br>

#### NeuroMorph Naming  
[Download](https://raw.githubusercontent.com/ajorstad/NeuroMorph/master/NeuroMorph_Other_Tools/NeuroMorph_Naming.py)  
[Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Other_Tools)  

Previously part of the deprecated NeuroMorph Measurement Tools, allows objects to be named according to a naming convention developed for neural structures.  
<br>

#### IMOD to Blender (correct_Y_mirroring.py)
[Download](https://raw.githubusercontent.com/ajorstad/NeuroMorph/master/NeuroMorph_Other_Tools/correct_Y_mirroring.py)  
[Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Other_Tools)  

Tool to correct IMOD-exported meshes by rotating in the Y dimension, so that they can be processed correctly in Blender.  See the [Full Documentation](https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/NeuroMorph/Other_Tools) for a description of the complete pipeline for importing IMOD meshes into Blender.


[![Analytics](https://ga-beacon.appspot.com/UA-99596205-1/NeuroMorph_Other_Tools?pixel)](https://github.com/ajorstad/NeuroMorph/tree/master/NeuroMorph_Other_Tools)
