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
        #dev = openni2.Device.open_file(video_path)
        get_file = get_filenames(video_path)
        extension = ".oni"
        get_file = video_path + "\\" + get_file[0]
        print(get_file)
        args = get_file
        dev = openni2.Device.open_file(args.encode('utf-8'))
        print("pbs")
        pbs = openni2.PlaybackSupport(dev)

        pbs.set_repeat_enabled(True)
        pbs.set_speed(-1.0)

        return dev, pbs
    except Exception as ex:
        print(ex)
        raise Exception("Initialization Error")

def processDepth(dev,pbs,interval,dst):
    try:
        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        depth_scale_factor = 255.0 / (650.0-520.0)
        depth_scale_beta_factor = -520.0*255.0/(650.0-520.0)
        nframes = depth_stream.get_number_of_frames()
        print("Depth frames: " + str(nframes))
        with open('timestampsdepth.txt', 'w') as tfile:
            for i in range(1, nframes+1, interval):
                try:
                    if i != nframes:
                        pbs.seek(depth_stream, i)    #Seek hangs if last frame is empty, sometimes happens
                except Exception as ex:
                    print("Error on depth stream seek ", ex)
                    continue
                s = openni2.wait_for_any_stream([depth_stream], 2)
                if s != depth_stream:
                    print("Error on depth stream, timeout reached reading frame n: ", str(i))
                    continue
                frame_depth = depth_stream.read_frame()
                frame_depth_data = frame_depth.get_buffer_as_uint16()
                depth_array = np.ndarray((frame_depth.height, frame_depth.width), dtype=np.uint16,
                                         buffer=frame_depth_data)
                depth_uint8 = depth_array*depth_scale_factor+depth_scale_beta_factor
                depth_uint8[depth_uint8 > 255] = 255
                depth_uint8[depth_uint8 < 0] = 0
                depth_uint8 = depth_uint8.astype('uint8')
                cv2.imwrite(dst + "/" + str(frame_depth.frameIndex) + "_16bit.png", depth_array)
                cv2.imwrite(dst + "/" + str(frame_depth.frameIndex) + "_8bit.png", depth_uint8)
                tfile.write(str(frame_depth.frameIndex) + ';' + str(frame_depth.timestamp) + '\n')
        depth_stream.close()
        print("All depth frames extracted")
    except Exception as ex:
        print(ex)

def processColor(dev,pbs,interval,dst):
    try:
        color_stream = dev.create_color_stream()
        color_stream.start()
        nframes = color_stream.get_number_of_frames()
        print("Color frames: " + str(nframes))
        with open('timestampscolor.txt', 'w') as tfile:
            for i in range(1, nframes+1, interval):
                try:
                    if i != nframes:
                        pbs.seek(color_stream, i)  # Seek hangs if last frame is empty, sometimes happens
                except Exception as ex:
                    print("Error on color stream seek ", ex)
                    continue
                s = openni2.wait_for_any_stream([color_stream], 2)
                if s != color_stream:
                    print("Error on color stream, timeout reached reading frame n: ", str(i))
                    continue
                frame_color = color_stream.read_frame()
                frame_color_data = frame_color.get_buffer_as_uint8()
                color_array = np.ndarray((frame_color.height, frame_color.width, 3), dtype=np.uint8,
                                         buffer=frame_color_data)
                color_array = cv2.cvtColor(color_array, cv2.COLOR_BGR2RGB)
                cv2.imwrite(dst + "/" + str(frame_color.frameIndex) + "_color.png", color_array)
                tfile.write(str(frame_color.frameIndex) + ';' + str(frame_color.timestamp) + '\n')
        color_stream.close()
        print("All color frames extracted")
    except Exception as ex:
        print(ex)

def main():
    print("Starting")
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="")
    p.add_argument('--v', dest='video_path', action='store', required=False, help='path Video')
    p.add_argument('--d', dest='dst', action='store', default='img', help='Destination Folder')
    p.add_argument('--i', dest='interval', action='store', default=1, help='Interval')
    print("Parsing arguments")
    args = p.parse_args()
    interval = int(args.interval)
    dst = args.dst
    if not os.path.exists(dst):
        os.mkdir(dst)
        print("Directory ", dst, " Created ")
    try:
        pathTest =  input("Path to video (with extension!): ")
        print("Initializing OpenNI2")

        distribute_files(pathTest)
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
    except Exception as ex:
        print("bad: ", ex)
    openni2.unload()

def create_folders(root_dir):
    pattern = '*.oni'
    files = []
    for file in os.listdir(root_dir):
        if fnmatch(file, pattern):
            files.append(file)
            try:
                output_folder = os.path.join(root_dir, os.path.splitext(file)[0])
                os.makedirs(output_folder)
            except:
                print("Folder already exists")
    return files
    

def get_filenames(root_dir):
    pattern = '*.oni'
    files = []
    for file in os.listdir(root_dir):
        if fnmatch(file, pattern):
            files.append(file)    
    return files

def distribute_files(root_dir):
    files = get_filenames(root_dir)
    file_extension = '.oni'
    print(root_dir)
    for file in files:
        folder = os.path.join(root_dir, file)
        if os.path.isfile(folder):
            file_name, file_extension = os.path.splitext(file)
            folder_name = os.path.join(root_dir, file_name)
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            shutil.move(folder, folder_name)
            print("File moved to folder: ", folder_name)
            core(folder_name)
            
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
if __name__ == '__main__':
    main()
