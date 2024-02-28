import os
from Structure.Robot import Mul_RB

# CLEAN PYC
os.system('pyclean .')

# PATH CONFIG MODEL
PATH_CONFIG_MUL_RB = './Config'

# CREATE MULTI ROBOT
mul = Mul_RB(PATH_CONFIG_MUL_RB)
