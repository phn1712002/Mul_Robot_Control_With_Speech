import os
from Device.Peripherals import Camera


#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')

cam = Camera(COM=0)
stop = False
while not(stop):
  frame = cam.getFrame()
  stop = cam.liveView(frame)