Here you can find example 3D mesh objects and an image stack for use with the NeuroMorph Toolkit.


#### NeuroMorph_sample.blend  ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Samples/NeuroMorph_sample.blend))
This is a blender file that contains a number of axons, dendrites and synapses that were reconstructed, using 
ilastik, from a downsampled series of images from the EM_stack folder.

*(Open this file in Blender.)*


#### EM_stack folder  ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/tree/master/NeuroMorph_Samples/EM_stack))
Contains 272 serial tiff images. These are serial electron micrographs taken with a focused ion beam scanning electron microscope. Each image is
700 pixels by 700 pixels, and each pixel has a dimension of 5 x 5 nm, so the width of each image is 3500 nm.  The pixels have a depth of 7.4 nm.

*(For use as the source folder using the NeuroMorph_Image_Stack_Interactions.py add-on with NeuroMorph_sample.blend.)*


#### sample_object_files folder  ([download](http://dstats.net/download/http://github.com/ajorstad/NeuroMorph/raw/master/NeuroMorph_Samples/sample_object_files.zip))
Contains 3 obj. files (ex13.obj; ex10.obj; ex08.obj) that have been exported from the ilastik software. They are models of dendrites and can be imported 
into the Blender software. The models were reconstructed from the stack of images provided in the EM_stack folder, however, they were downsampled to 
300 x 300 pixels. Therefore the size of each pixel is (3.5 divided by 300) 0.01167 microns. When importing into blender, use 0.01167 in the ‘Scale’ box 
of the ‘import objects’ tool.

*(For use with NeuroMorph_Import_Objects.py add-on.)*
