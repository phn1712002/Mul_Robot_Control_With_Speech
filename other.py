from Structure.Robot import Robot_V1


rb = Robot_V1('Config\config_RB_2.json')
while True:
  rb.controlOneLink(2, 50)
  rb.controlOneLink(1, 50)
  rb.controlOneLink(1, -50)
  rb.controlOneLink(2, -50)