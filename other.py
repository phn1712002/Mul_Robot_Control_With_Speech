import os, random
from Structure.Robot import Robot_V1
os.system('pyclean .')
rb = Robot_V1('Config\config_RB_1.json')
while True:
  link = random.randint(0, 2)
  angle = random.randint(-90, 90)
  rb.controlOneLink(link, angle)