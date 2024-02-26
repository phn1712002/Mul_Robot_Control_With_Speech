import os
import cv2
import uuid

def saveImage(directory:str, image, overwrite=False):
    """
    Save an image using OpenCV with a random filename

    Parameters:
    image (numpy.ndarray): The image to save
    directory (str): The directory where to save the image
    overwrite (bool): Whether to overwrite the existing file
    """
    # Check if directory is a file path or a directory
    if '.' in os.path.basename(directory):  # It's a file path
        path = directory
        dir_name = os.path.dirname(directory)
        if not overwrite and os.path.exists(path):  # File exists and we don't want to overwrite
            filename = str(uuid.uuid4()) + '.png'
            path = os.path.join(dir_name, filename)
    else:  # It's a directory
        dir_name = directory
        filename = str(uuid.uuid4()) + '.png'
        path = os.path.join(directory, filename)

        # If file exists, generate a new filename
        while os.path.exists(path):
            filename = str(uuid.uuid4()) + '.png'
            path = os.path.join(directory, filename)

    # Check if directory exists, if not, create it
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Save the image
    return cv2.imwrite(path, image)

def writeText(image, text, 
              position='top_left', 
              font=cv2.FONT_HERSHEY_SIMPLEX, 
              font_scale=1, 
              color='white', 
              thickness=2):
    """
    Write text on an image using OpenCV

    Parameters:
    image (numpy.ndarray): The image to write text on
    text (str): The text to write
    position (str or tuple): The position where to write the text
    font (cv2.FONT): The font to use
    font_scale (float): The font scale
    color (str or tuple): The color of the text
    thickness (int): The thickness of the text
    """
    
    colors = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'cyan': (255, 255, 0),
        'magenta': (255, 0, 255),
        'silver': (192, 192, 192),
        'gray': (128, 128, 128),
        'maroon': (0, 0, 128),
        'olive': (0, 128, 128),
        'purple': (128, 0, 128),
        'teal': (128, 128, 0),
        'navy': (128, 0, 0)
    }

    positions = {
        'center': (image.shape[1] // 2, image.shape[0] // 2),
        'top_left': (0, 0),
        'top_right': (image.shape[1], 0),
        'bottom_left': (0, image.shape[0]),
        'bottom_right': (image.shape[1], image.shape[0]),
        'top_center': (image.shape[1] // 2, 0),
        'bottom_center': (image.shape[1] // 2, image.shape[0]),
        'middle_left': (0, image.shape[0] // 2),
        'middle_right': (image.shape[1], image.shape[0] // 2)
    }

    # If color is a string, get the corresponding BGR tuple
    if isinstance(color, str):
        color = colors.get(color, color)

    # If position is a string, get the corresponding position tuple
    if isinstance(position, str):
        position = positions.get(position, position)

    return cv2.putText(image, text, position, font, font_scale, color, thickness)