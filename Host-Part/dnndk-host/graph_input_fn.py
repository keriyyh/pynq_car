'''
@Author: sauron
@Date: 2019-10-29 15:33:55
@LastEditTime : 2019-12-18 17:51:26
@LastEditors  : Sauron Wu
@Description: In User Settings Edit
@FilePath: /pynq_car/Host-Part/dnndk-host/graph_input_fn.py
'''
import cv2
from PIL import Image
import os
import numpy as np

CONV_INPUT = "input_1"
calib_batch_size = 50

path = "/home/xilinx/dnndk-pynqz2/yolo_keras/prepare_training_data/trainData/images/"
#image = cv2.imread(path + "/data/dog.jpg")
#img = cv2.resize(image,(416,416),cv2.INTER_AREA)

def letterbox_image(image, size):
        '''resize image with unchanged aspect ratio using padding'''
        iw, ih = image.size
        w, h = size
        scale = min(w/iw, h/ih)
        nw = int(iw*scale)
        nh = int(ih*scale)

        image = image.resize((nw,nh), Image.BICUBIC)
        new_image = Image.new('RGB', size, (128,128,128))
        new_image.paste(image, ((w-nw)//2, (h-nh)//2))
        return new_image
def calib_input(iter):
  images = []
  path = "/home/xilinx/Host-Part/images/"
  files = os.listdir(path)
  for index in range(0, calib_batch_size):
      image = Image.open(path+files[index])
      boxed_image = letterbox_image(image,(416,416))
      image_data = np.array(boxed_image, dtype='float32')
      #print(image_data.shape)
      image_data /= 256.
      images.append(image_data)
  return {CONV_INPUT: images}

