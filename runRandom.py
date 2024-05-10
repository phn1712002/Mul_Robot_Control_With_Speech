import os
from Structure.Robot import Mul_RB

#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')

#! PATH MODEL MODELr
PATH_CONFIG_MUL_RB = './Config/'

#! CREATE MULTI ROBOT
mul = Mul_RB(PATH_CONFIG_MUL_RB)
mul.runRandom()
 