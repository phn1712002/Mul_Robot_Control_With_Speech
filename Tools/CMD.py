import os

def clearCMD():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
