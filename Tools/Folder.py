import os, glob

def getPathInFolder(path):
    files = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def getFileWithPar(path, name_file='config_RB_*.json'):
    file_with_par = os.path.join(path, name_file)
    files = glob.glob(file_with_par)
    return files
