import os
import sys
import cv2
#from cv2 import cv2
from openni import openni2
import argparse
import numpy as np
from fnmatch import fnmatch
import shutil

def openDevice(video_path):
    print("Opening device")
    try:
        if sys.platform == "win32":
            libpath = "lib/Windows"
        else:
            libpath = "lib/Linux"
        openni2.initialize(libpath)
        
        #getting file name and put in the args to open the device and start the stream  
        get_file = get_filenames(video_path)
        get_file = video_path + "\\" + get_file[0] # get the files 1 by one to process them, get_file[0] is an argument for read the index of the array to append for file path, does not mean the first file!
        print("full file path: " ,get_file)
        args = get_file
        #open device
        #dev = openni2.Device.open_file(video_path) 
        dev = openni2.Device.open_file(args.encode('utf-8'))
        print("playback support (pbs)")
        pbs = openni2.PlaybackSupport(dev) # playback support

        pbs.set_repeat_enabled(True)
        pbs.set_speed(-1.0)

        return dev, pbs
    except Exception as ex:
        print(ex)
        raise Exception("Initialization Error")
#process function after creating folder and move the files to the folder with the same name as the file
def processDepth(dev,pbs,interval,dst):
    try:
        depth_stream = dev.create_depth_stream() # depth camera
        depth_stream.start() # start the stream
        depth_scale_factor = 255.0 / (650.0-520.0)# 8-bit scaling factor
        depth_scale_beta_factor = -520.0*255.0/(650.0-520.0) # 8-bit scaling factor
        nframes = depth_stream.get_number_of_frames()# get number of frames
        print("Depth frames: " + str(nframes)) # print number of frames
        with open('timestampsdepth.txt', 'w') as tfile: # write timestamps to txt file
            for i in range(1, nframes+1, interval): # iterate through frames
                try:
                    if i != nframes:
                        pbs.seek(depth_stream, i)    #Seek hangs if last frame is empty, sometimes happens
                except Exception as ex:
                    print("Error on depth stream seek ", ex)
                    continue
                s = openni2.wait_for_any_stream([depth_stream], 2) # wait for stream
                if s != depth_stream:
                    print("Error on depth stream, timeout reached reading frame n: ", str(i))
                    continue
                frame_depth = depth_stream.read_frame() # read frame
                frame_depth_data = frame_depth.get_buffer_as_uint16() # get buffer as 16 bit
                depth_array = np.ndarray((frame_depth.height, frame_depth.width), dtype=np.uint16,
                                         buffer=frame_depth_data) # create array
                depth_uint8 = depth_array*depth_scale_factor+depth_scale_beta_factor # scale array to 8 bit
                depth_uint8[depth_uint8 > 255] = 255 # set max value to 255
                depth_uint8[depth_uint8 < 0] = 0 # set min value to 0
                depth_uint8 = depth_uint8.astype('uint8') # set type to uint8
                cv2.imwrite(dst + "/" + str(frame_depth.frameIndex) + "_16bit.png", depth_array)# save 16 bit image
                cv2.imwrite(dst + "/" + str(frame_depth.frameIndex) + "_8bit.png", depth_uint8)# save 8 bit image
                tfile.write(str(frame_depth.frameIndex) + ';' + str(frame_depth.timestamp) + '\n')#  write timestamps to txt file
        depth_stream.close() # close stream
        print("All depth frames extracted")
    except Exception as ex:
        print(ex)

def processColor(dev,pbs,interval,dst): # process color frames
    try:
        color_stream = dev.create_color_stream() # color camera
        color_stream.start() # start stream
        nframes = color_stream.get_number_of_frames() # get number of frames
        print("Color frames: " + str(nframes)) # print number of frames
        with open('timestampscolor.txt', 'w') as tfile: # write timestamps to txt file
            for i in range(1, nframes+1, interval): # iterate through frames
                try:
                    if i != nframes:
                        pbs.seek(color_stream, i)  # Seek hangs if last frame is empty, sometimes happens
                except Exception as ex:
                    print("Error on color stream seek ", ex)
                    continue
                s = openni2.wait_for_any_stream([color_stream], 2) # wait for stream
                if s != color_stream:
                    print("Error on color stream, timeout reached reading frame n: ", str(i))
                    continue
                frame_color = color_stream.read_frame() # read frame
                frame_color_data = frame_color.get_buffer_as_uint8() # get buffer as 8 bit
                color_array = np.ndarray((frame_color.height, frame_color.width, 3), dtype=np.uint8,
                                         buffer=frame_color_data) # create array
                color_array = cv2.cvtColor(color_array, cv2.COLOR_BGR2RGB) # convert to RGB
                cv2.imwrite(dst + "/" + str(frame_color.frameIndex) + "_color.png", color_array) # save image
                tfile.write(str(frame_color.frameIndex) + ';' + str(frame_color.timestamp) + '\n') # write timestamps to txt file
        color_stream.close()
        print("All color frames extracted")
    except Exception as ex:
        print(ex)

def main():
    print("Starting")
    #arguments for reference, only the path is used, --d is destination folder, --i is interval (step of processing frames, default 1)
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="")
    p.add_argument('--v', dest='video_path', action='store', required=False, help='path Video')
    p.add_argument('--d', dest='dst', action='store', default='img', help='Destination Folder')
    p.add_argument('--i', dest='interval', action='store', default=1, help='Interval')
    print("Parsing arguments")
    args = p.parse_args() # parse arguments
    interval = int(args.interval)
    dst = args.dst
    #creating destination folder, not used
    if not os.path.exists(dst):
        os.mkdir(dst)
        print("Directory ", dst, " Created ")
    #core code
    try:
        pathTest =  input("Path to video or videos: ")
        print("Initializing OpenNI2")

        distribute_files(pathTest) # start extraction

        
    except Exception as ex:
        print("bad: ", ex)
    openni2.unload()
#func to create folders with matched files, reserve function in case of lost code or mismatch in the future
def create_folders(root_dir):
    pattern = '*.oni'
    files = []
    for file in os.listdir(root_dir):
        if fnmatch(file, pattern): # if file matches pattern
            files.append(file)
            try:
                output_folder = os.path.join(root_dir, os.path.splitext(file)[0]) # create folder with same name as file
                os.makedirs(output_folder)
            except:
                print("Folder already exists")
    return files
    
#func to get filenames with extension for further processing and creating folders with matched files
def get_filenames(root_dir):
    pattern = '*.oni'
    files = []
    for file in os.listdir(root_dir):
        if fnmatch(file, pattern):
            files.append(file)    
    return files

#func to distribute files to folders with matched names and start extracting the frames
def distribute_files(root_dir):
    files = get_filenames(root_dir)
    file_extension = '.oni'
    print("root folder: ", root_dir)
    #iteration through files in root folder if the path doesnt exist he will be created, if not he will be skipped, if the file is a file it will be moved to the folder with the same name as the file
    for file in files:
        folder = os.path.join(root_dir, file)
        if os.path.isfile(folder):
            file_name, file_extension = os.path.splitext(file)
            folder_name = os.path.join(root_dir, file_name)
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            shutil.move(folder, folder_name)
            print("File moved to folder: ", folder_name)
            #extraction starts here
            core(folder_name)
#core function with core code, the most important part of the script using openni2 library to extract the frames see more info in: https://structure.io/openni            
def core(folder_name):
    dev, pbs = openDevice(folder_name)
    print("Device Opened")
    if dev.has_sensor(openni2.SENSOR_COLOR):
        print("Color Stream found")
        processColor(dev, pbs)
    if dev.has_sensor(openni2.SENSOR_DEPTH):
        print("Depth Stream found")
        processDepth(dev, pbs,1,folder_name)
    print("Done!")

#kick function to start the script
if __name__ == '__main__':
    main()


#in case some of the functions above will be needed in the future

""" # core code
        dev, pbs = openDevice(pathTest.encode('utf-8'))
        print("Device Opened")
        if dev.has_sensor(openni2.SENSOR_COLOR):
            print("Color Stream found")
            processColor(dev, pbs, interval, dst)
        if dev.has_sensor(openni2.SENSOR_DEPTH):
            print("Depth Stream found")
            processDepth(dev, pbs, interval, dst)
        print("Done!")
        """