import os, random
from Structure.Robot import Robot_V1

#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')

#! CREATE MULTI ROBOT
rb = Robot_V1('Config\config_RB_1.json')
while True:
  rb.controlOneLink(0, -55)
  rb.controlOneLink(1, 30)
  rb.controlOneLink(1, -30)
  rb.controlOneLink(0, 55)