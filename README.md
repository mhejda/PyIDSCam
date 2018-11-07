# PyIDSCam
Simple Python3 module to allow basic, quick operation of some features on the IDS Cameras.

**Requirements**

This module uses the pyueye module from IDS in the back-end. numpy package is needed for proper function and scikit-image is optionally used for image resizing.

**USE**

Simply download the IDSCamera.py file, locate it in a directory where python finds it (or working directory), then load it using:

   from IDSCamera import IDSCam

Then, initialize the class:

   camera = IDSCam()

Camera is automatically connected during the initialization phase. Image can be then captured using function:

   RGGBimages = camera.capture_image()

The module is designed for scientific imaging: for that reason, all of the image enhancements functions are disabled and RAW images are queried from the buffer. The camera function 'capture_image' returns a dictionary with four entries: R,G1,G2,B - each of these representing the group of single colored pixels in the camera. For monochromatic cameras, the same dictionary is returned, but all the entries are the same.

This code is meant to help you quickly connect to an IDS Camera and give you an idea of how to control it via Python3. The code is fairly simplistic and should be easily modifyable to suit your own needs.

I'll gladly help with using/modifiying/bugfixing, just let me know.