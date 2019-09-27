'''
@Author: Sauron Wu
@GitHub: wutianze
@Email: 1369130123qq@gmail.com
@Date: 2019-09-23 10:12:28
@LastEditors: Sauron Wu
@LastEditTime: 2019-09-27 16:03:35
@Description: 
'''
#!/usr/bin/env python
'''
Predict Server
Create a server to accept image inputs and run them against a trained neural network.
This then sends the steering output back to the client.
Author: Tawn Kramer
'''
#from __future__ import print_function
import os
import argparse
import json
import time
import asyncore
import socket
from io import BytesIO
import base64
import datetime
import tensorflow as tf

import numpy as np
from keras.models import load_model
from PIL import Image

from tcp_server import IMesgHandler, SimServer

class PynqSimMsgHandler(IMesgHandler):

    def __init__(self, model, port=0, num_cars=1, rand_seed=0, process_method=0, control_method=0):
        self.model = model
        self.graph = tf.get_default_graph()
        #self.constant_throttle = constant_throttle
        self.sock = None
        self.image_folder = None
        self.steering_angle = 0.
        self.throttle = 0.
        self.num_cars = 0
        self.port = port
        self.target_num_cars = num_cars
        self.rand_seed = rand_seed
        self.process_method = process_method
        self.control_method = control_method
        self.fns = {'telemetry' : self.on_telemetry,\
                    'car_loaded' : self.on_car_created,\
                    'on_disconnect' : self.on_disconnect}

    def on_connect(self, socketHandler):
        self.sock = socketHandler

    def on_disconnect(self):
        self.num_cars = 0

    def on_recv_message(self, message):
        if not 'msg_type' in message:
            print('expected msg_type field')
            return

        msg_type = message['msg_type']
        if msg_type in self.fns:
            self.fns[msg_type](message)
        else:
            print('unknown message type', msg_type)

    def on_car_created(self, data):
        if self.rand_seed != 0:
            self.send_regen_road(0, self.rand_seed, 1.0)

        self.num_cars += 1
        if self.num_cars < self.target_num_cars:
            print("requesting another car..")
            self.request_another_car()

    def on_telemetry(self, data):
        imgString = data["image"]
        image = Image.open(BytesIO(base64.b64decode(imgString)))
        image_array = np.asarray(image)
        if self.process_method == 0:
            image_array = image_array/255.0
        elif self.process_method == 1:
            image_array = image_array/255.0 - 0.5
        elif self.process_method == 2:
            image_array = image_array/127.5 - 1.0
        elif self.process_method == 3:
            image_array = image_array/102.83 - 1.0
        elif self.process_method == 4:
            image_array = image_array[40:,:]
        #print(image_array)
        self.predict(image_array)

        # maybe save frame
        if self.image_folder is not None:
            timestamp = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
            image_filename = os.path.join(self.image_folder, timestamp)
            image.save('{}.jpg'.format(image_filename))


    def predict(self, image_array):
        with self.graph.as_default():
            outputs = self.model.predict(image_array[None, :, :, :])
        #outputs = np.array([0,1,0,0])
        #rint("predict outputs")
        #print(outputs)
        self.parse_outputs(outputs)
    
    def parse_outputs(self, outputs):
        res = []
        for output in outputs:            
            for i in range(output.shape[0]):
                res.append(output[i])

        self.on_parsed_outputs(res)

    def on_parsed_outputs(self, outputs):
        #print(self.control_method)
        if self.control_method == 0:
            comSend = ''
            toSend = 0
            nowMax = 0.0
            for i in range(len(outputs)):
                if outputs[i] > nowMax:
                    nowMax = outputs[i] 
                    toSend = i
            if toSend == 0:
                comSend = 'a'
            elif toSend == 1:
                comSend = 'w'
            elif toSend == 2:
                comSend = 'd'
            else:
                comSend = 's'
            self.send_control0(comSend)
        elif self.control_method == 1:
            #print("on parsed outputs")
            #print(outputs)
            self.send_control1(outputs[0], 0.3)
        elif self.control_method == 2:
            #print("on parsed outputs")
            #print(outputs)
            self.send_control1(outputs[0], outputs[1])

        
    def send_control0(self, command):
        msg = { 'msg_type' : 'pynq_control', 'command':command[0] }
        self.sock.queue_message(msg)

    def send_control1(self, steer, throttle):
        #print("steer outputs")
        print(steer)
        msg = { 'msg_type' : 'control', 'steering': steer.__str__(), 'throttle':throttle.__str__(), 'brake': '0.0' }
        self.sock.queue_message(msg)

    def send_regen_road(self, road_style=0, rand_seed=0, turn_increment=0.0):
        '''
        Regenerate the road, where available. For now only in level 0.
        In level 0 there are currently 5 road styles. This changes the texture on the road
        and also the road width.
        The rand_seed can be used to get some determinism in road generation.
        The turn_increment defaults to 1.0 internally. Provide a non zero positive float
        to affect the curviness of the road. Smaller numbers will provide more shallow curves.
        '''
        msg = { 'msg_type' : 'regen_road',
            'road_style': road_style.__str__(),
            'rand_seed': rand_seed.__str__(),
            'turn_increment': turn_increment.__str__() }
        
        self.sock.queue_message(msg)

#    def request_another_car(self):
#        port = self.port + self.num_cars
#        address = ("0.0.0.0", port)
#        
#        #spawn a new message handler serving on the new port.
#        handler = PynqSimMsgHandler(self.model, 0., num_cars=(self.target_num_cars - 1), port=address[1])
#        server = SimServer(address, handler)
#
#        msg = { 'msg_type' : 'new_car', 'host': '127.0.0.1', 'port' : port.__str__() }
#        self.sock.queue_message(msg)   

    def on_close(self):
        pass

def go(filename, address, constant_throttle=0, num_cars=1, image_cb=None, rand_seed=None, process_method=0,control_method=0):

    model = load_model(filename)

    #looks like we have to compile it before use. These optimizers don't matter for inference.
    model.compile("sgd", "mse")
  
    #setup the server
    #handler = DonkeySimMsgHandler(model, constant_throttle, port=address[1], num_cars=num_cars, image_cb=image_cb, rand_seed=rand_seed)
    #model = None
    #print(control_method)
    handler = PynqSimMsgHandler(model, process_method=process_method,control_method=control_method)
    server = SimServer(address, handler)

    try:
        #asyncore.loop() will keep looping as long as any asyncore dispatchers are alive
        asyncore.loop()
    except KeyboardInterrupt:
        #unless some hits Ctrl+C and then we get this interrupt
        print('stopping')

# ***** main loop *****
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='prediction server')
    parser.add_argument('--model', type=str, help='model filename')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='bind to ip')
    parser.add_argument('--port', type=int, default=9090, help='bind to port')
    parser.add_argument('--num_cars', type=int, default=1, help='how many cars to spawn')
    parser.add_argument('--constant_throttle', type=float, default=0.0, help='apply constant throttle')
    parser.add_argument('--rand_seed', type=int, default=0, help='set road generation random seed')
    parser.add_argument('--process_method', type=int, default=0, help='process method like in process_img')
    parser.add_argument('--control_method', type=int, default=0, help='0 for command, 1 for steer')
    args = parser.parse_args()

    address = (args.host, args.port)
    #print(args.control_method)
    go(args.model, address, args.constant_throttle, num_cars=args.num_cars, rand_seed=args.rand_seed,process_method=args.process_method,control_method=args.control_method)
