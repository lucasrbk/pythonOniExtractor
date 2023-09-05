# pythonOniExtractor
frame extractor for OpenNI2 .Oni

Version more easy to use, don't need command line, tested in Windows 10 but also works on ubuntu. OpenNI2 library are contained in the folder lib and comes from Orbbec (version 05/09/2023).

Frames are saved in img folder inside project folder.

Depth frames are saved in the original format (16bit grayscale not working) and in a more readable format, scaled to 8 bit and multiplied by a factor plus an offset (with also cast saturation). You can change this values in the code, they dependent by the max and min values of the depths.

Name of the saved images contain the frame ID, which in case of synchronization was enabled in the recording can be used to match color and depth frames.

# Requirements:
Python 3 32bit (or above), with the following packages (you can install them using pip):

openni
numpy
opencv 3 (opencv-python) 
example: pip install opencv-python

OBS: if opencv doesn't works use "opencv-contrib-python" in command line to install instead.


#Use 
In this version you need just to run the code and put path with file and extension.
Example: C:\Users\[YOURUSER]\pyOniExtractor\sample\sample.oni

# Acknowledgements
This works is from https://github.com/rokopi-byte, i just update it and add make more easy to use
