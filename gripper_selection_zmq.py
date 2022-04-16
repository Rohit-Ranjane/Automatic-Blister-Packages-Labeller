#!/usr/bin/env python3

import cv2 as cv
import open3d as o3d

import zmq
import time
import os
import sys
from pathlib import Path
from pprint import pprint




 # Creates a socket instance
context = zmq.Context() # Edit test comment
socket = context.socket(zmq.PUB)    
socket1 = context.socket(zmq.SUB)
socket2 = context.socket(zmq.SUB)
socket3 = context.socket(zmq.SUB)

    # Binds the socket to a predefined port on localhost, 'Socket' for publishing data, 'Socket1' for receiving data from group B, 'Socket2' for receiving data from point cloud       generator and 'socket3 for receiving data from image generator'
 
    #Takes the information regarding IP address and Port for new tray detector 

socket1_ip = input ("Enter New_tray_detectors_IP : ")
socket1_port = input("Enter port number : ")
print("The Socket1 has IP :", socket1_ip," and Port : ", socket1_port)
    
    #Takes the information regarding IP address and Port for PCD Generator

socket2_ip = input ("Enter IP of PCD Generator : ")
socket2_port = input("Enter port number : ")
print("The Socket2 has IP :", socket2_ip," and Port : ", socket2_port)

    #Takes the information regarding IP address and Port for Image Generator

socket3_ip = input ("Enter IP of Image  Generator : ")
socket3_port = input("Enter port number : ")
print("The Socket2 has IP :", socket3_ip," and Port : ", socket3_port)

socket.bind("tcp://127.0.0.1:5001")
socket1.connect("tcp://{}:{}".format(socket1_ip, socket1_port))
socket1.subscribe("")
socket2.connect("tcp://{}:{}".format(socket2_ip, socket2_port))
socket2.subscribe("")
socket3.connect("tcp://{}:{}".format(socket3_ip, socket3_port))
socket3.subscribe("")

print("connection complete....")




print("Searching for weight and configuration files..")

for root, dirs, files in os.walk('/build/'):
    for file_RGB_weight in files:
        if file_RGB_weight.endswith('yolov4_rgb.weights'):
            Path_RGB_weight = str(root) + '/' + 'yolov4_rgb.weights'
            print('RGB Weight file found at : ' + str(root) + '/' + 'yolov4_rgb.weights')

for root, dirs, files in os.walk('/build/'):
    for file_RGB_cfg in files:
        if file_RGB_cfg.endswith('yolov4_custom_rgb.cfg'): 
            Path_RGB_cfg = str(root) + '/' + 'yolov4_custom_rgb.cfg'
            print('RGB Configuration file found at : ' + str(root) + '/' + 'yolov4_custom_rgb.cfg')


for root, dirs, files in os.walk('/build/'):
    for file_PCD_weight in files:
        if file_PCD_weight.endswith('yolov4_pcd.weights'):
            Path_PCD_weight = str(root) + '/' + 'yolov4_pcd.weights'
            print('PCD Weight file found at : ' + str(root) + '/' + 'yolov4_pcd.weights')

for root, dirs, files in os.walk('/build/'):
    for file_PCD_cfg in files:
        if file_PCD_cfg.endswith('yolov4_custom_pcd.cfg'): 
            Path_PCD_cfg = str(root) + '/' + 'yolov4_custom_pcd.cfg'
            print('PCD Configuration file found at : ' + str(root) + '/' + 'yolov4_custom_pcd.cfg')


while (1):

    Rank_final = []


    # get new tray info using ZMQ protocol and write to new tray variable
    new_tray = socket1.recv_string()
  
    print('Waiting for new tray status')

    if new_tray == '1':

        print("New tray identified")


        path = Path().absolute()
         
        if not os.path.exists(str(path) +'/' + 'Project/'):
               os.makedirs(str(path) +'/' + 'Project/') 
               print("New project folder created") 

        # Renames the newly received files
        
        path1 = str(path) +'/' + 'Project/'
        filename1 = 'PC' + '.txt'
        destfile1 = path1 + '/' + filename1

        filename2 = 'Image' + '.jpg'
        destfile2 = path1 + '/' + filename2

        filename3 = 'PC_mod' + '.txt'
        destfile3 = path1 + '/' + filename3

        destfile4 = Path_RGB_weight
        destfile5 = Path_RGB_cfg
        destfile6 = Path_PCD_weight
        destfile7 = Path_PCD_cfg
        
        
        # checks if the file is previously present, if yes it removes it
        if os.path.isfile(destfile1):
           os.remove(destfile1)

        if os.path.isfile(destfile2):
           os.remove(destfile2)
           time.sleep(2)

        # receives the file, size chunk set to 25MB
        print("Receiving files")
        msg1 = socket2.recv(25000000)
        time.sleep (5)
        print("PCD Data received")
        msg2 = socket3.recv(25000000)
        time.sleep (5)   
        print("RGB Image received")

        # writes the received data in the destination file set above
        if msg1: 
           f = open(destfile1, 'wb')
           f.write(msg1)
           size1 = os.stat(destfile1).st_size
           print('File size:', size1)
           f.close()

        if msg2: 
           f1 = open(destfile2, 'wb')
           f1.write(msg2)
           size2= os.stat(destfile2).st_size
           print('File size:', size2)
           f1.close()
        
        print("File write complete")

        file_in = open(destfile1, "rt")
        file_out = open(destfile3, "wt")

        for line in file_in:
            file_out.write(line.replace(';', ' '))
        file_in.close()
        file_out.close()

        read_points = o3d.io.read_point_cloud(destfile3, format="xyzn")
        read_points.estimate_normals()
        reference = o3d.geometry.TriangleMesh.create_coordinate_frame()  # reference frame for rotation
        read_points.rotate(reference.get_rotation_matrix_from_xyz((3.14 / 2, 0, 0)))  # rotate

        ###################################### Alpha shapes ###########################################
        Alpha_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(read_points, alpha = 9)
        Alpha_mesh.compute_vertex_normals()
        o3d.io.write_triangle_mesh("mesh.ply", Alpha_mesh) # Alpha shapes
        # o3d.visualization.draw_geometries([Alpha_mesh])
        #############################################################################################



        read_mesh = o3d.io.read_triangle_mesh("mesh.ply")
        sample_points = read_mesh.sample_points_uniformly(number_of_points=1000000)
        # o3d.visualization.draw_geometries([sample_points])
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        vis.get_render_option().point_color_option = o3d.visualization.PointColorOption.ZCoordinate
        vis.get_render_option().point_size = 4.0
        vis.add_geometry(sample_points)
        vis.capture_screen_image("depth_image.jpg", do_render=True)
        vis.destroy_window()


        classes = ['Three Jaw Gripper', 'Inner Gripper','Vacuum Gripper','Two Jaw Gripper']

        #Model Trained for PCD
        net_pcd = cv.dnn.readNetFromDarknet(destfile7,destfile6)

        #Model Trained for RGB
        net_rgb = cv.dnn.readNetFromDarknet(destfile5,destfile4)


        img_pcd = cv.imread('depth_image.jpg')
        img_rgb = cv.imread(destfile2)

        # Function to rank the detected gripper 

        def rankfunc(img,net):

            img = cv.resize(img, (1370, 749))
            height, width, _ = img.shape
            blob = cv.dnn.blobFromImage(img, 1 / 255, (416, 416), (0, 0, 0), swapRB=True, crop=False)

            net.setInput(blob)

            output_layers_name = net.getUnconnectedOutLayersNames()

            layerOutputs = net.forward(output_layers_name)

            boxes0,boxes1,boxes2,boxes3 = [],[],[],[]
            confidences0,confidences1,confidences2,confidences3 = [],[],[],[]

        # loop to identify the accuracy of the same detected object for each class

            for output in layerOutputs:
                for detection in output:
                    score = detection[5:]

                    if score[0] or score[1] or score[2] or score[3] > 0.5:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)

                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        
                        boxes0.append([x, y, w, h])
                        confidences0.append((float(score[0])))

                        
                        boxes1.append([x, y, w, h])
                        confidences1.append((float(score[1])))
                        
                        boxes2.append([x, y, w, h])
                        confidences2.append((float(score[2])))
                        
                        boxes3.append([x, y, w, h])
                        confidences3.append((float(score[3])))
                            


            indexes0 = cv.dnn.NMSBoxes(boxes0, confidences0, .8, .4)
            indexes1 = cv.dnn.NMSBoxes(boxes1, confidences1, .8, .4)
            indexes2 = cv.dnn.NMSBoxes(boxes2, confidences2, .8, .4)
            indexes3 = cv.dnn.NMSBoxes(boxes3, confidences3, .8, .4)

            item = (len(indexes0) + len(indexes1) + len(indexes2) + len(indexes3))
            index = [indexes0 , indexes1 , indexes2 , indexes3]
            confidence = [confidences0 , confidences1 ,confidences2 ,confidences3]

            Rank = []

            if len(index[0]) > 0:
                sum = 0
                for i in index[0].flatten():
                    sum += confidences0[i]
                Rank.append((round(sum/item, 2),0))
            else:
                Rank.append((0,0))
                
            if len(index[1]) > 0:
                sum = 0
                for i in index[1].flatten():
                    sum += confidences1[i]
                Rank.append((round(sum/item, 2),1))
            else:
                Rank.append((0,1))

            if len(index[2]) > 0:
                sum = 0
                for i in index[2].flatten():
                    sum += confidences2[i]
                Rank.append((round(sum/item, 2),2))
            else:
                Rank.append((0,2))

            if len(index[3]) > 0:
                sum = 0
                for i in index[3].flatten():
                    sum += confidences3[i]
                Rank.append((round(sum/item, 2),3))
            else:
                Rank.append((0,3))
            
            Rank.sort()

            return Rank

        # Output based on rank

        Rank_pcd = rankfunc(img_pcd,net_pcd)

        Rank_rgb = rankfunc(img_rgb,net_rgb)

        # final gripper Ranking Algorithm

        for i in range(0,4):
            for j in range(0,4):
                if Rank_pcd[i][1] == Rank_rgb[j][1]:
                    Rank_final.append(((Rank_pcd[i][0] + Rank_rgb[j][0])/2,Rank_pcd[i][1]))

        Rank_final.sort()

        # communication code for sending the selected gripper
        # Publishes the result to other groups

        Final_grip = Rank_final[3][1]
        print("Values for ranks of pcd")
	
        print(Rank_pcd)
        print("Values for ranks of rgb")
        print(Rank_rgb)
        
        socket.send_string(classes[Final_grip])
        print(Rank_final)
        print(classes[Final_grip])
     
        
    elif new_tray == '0' : 
           socket.send_string(classes[Final_grip])
           print(classes[Final_grip])
           print("Assigning previous gripper as same tray")                  
        

