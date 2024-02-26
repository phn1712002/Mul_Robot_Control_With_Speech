import json, os
 
def loadJson(path='./config.json', encoding='utf-8'):
    if os.path.exists(path):
        with open(path, 'r', encoding=encoding) as json_file:
            return json.load(json_file)
    else:
        raise RuntimeError('File error')
    

def saveJson(path='./config.json', data=None, encoding='utf-8'):
    with open(path, 'w', encoding=encoding) as json_file:
        json.dump(data, json_file, indent=4)
    return True

    