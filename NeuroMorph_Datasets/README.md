Here you can find example 3D mesh objects and an image stack for use with the NeuroMorph Toolkit.


#### NeuroMorph_sample.blend  ([download](http://github.com/NeuroMorph-EPFL/NeuroMorph/raw/master/NeuroMorph_Datasets/NeuroMorph_sample.blend))
A blender file containing axons, dendrites, and synapses that were reconstructed from the images in the EM_stack folder.

*(Open this file in Blender.)*


#### EM_stack folder  ([download](http://github.com/NeuroMorph-EPFL/NeuroMorph/tree/master/NeuroMorph_Datasets/EM_stack))
Image stack source folder for NeuroMorph_sample.blend.  Contains 272 serial tiff images in 2 zip files. These are serial electron micrographs taken with a focused ion beam scanning electron microscope. Each image is 700 pixels by 700 pixels, and each pixel has a dimension of 5 x 5 nm, so the width of each image is 3500 nm.  The pixels have a depth of 7.4 nm.  This corresponds to Image Stack Dimensions (microns) of x: 3.5, y: 3.5, z: 2.0.

*(For use as the image source folder using the NeuroMorph_3D_Drawing.py add-on,  
corresponds to the objects in NeuroMorph_sample.blend.)*


#### sample_object_files folder  ([download](http://github.com/NeuroMorph-EPFL/NeuroMorph/raw/master/NeuroMorph_Datasets/sample_object_files.zip))
Contains 3 obj. files (ex13.obj; ex10.obj; ex08.obj) that have been exported from the ilastik software. They are models of dendrites and can be imported 
into the Blender software. The models were reconstructed from the stack of images provided in the EM_stack folder, however, they were downsampled to 
300 x 300 pixels. Therefore the size of each pixel is (3.5 divided by 300) 0.01167 microns. When importing into blender, use 0.01167 in the ‘Scale’ box 
of the ‘import objects’ tool.

*(For use with NeuroMorph_Import_Objects.py add-on.)*

[![Analytics](https://ga-beacon.appspot.com/UA-99596205-1/NeuroMorph_Datasets?pixel)](https://github.com/NeuroMorph-EPFL/NeuroMorph/tree/master/NeuroMorph_Datasets)
