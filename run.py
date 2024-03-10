import os
from Structure.Robot import Mul_RB

#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')

#! PATH CONFIG MODEL
PATH_CONFIG_MUL_RB = './Config/'

#! CREATE MULTI ROBOT
mul = Mul_RB(PATH_CONFIG_MUL_RB)
mul.runHandle()
 