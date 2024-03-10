
import cv2, keyboard, tensorflow as tf, sounddevice as sd, numpy as np
from .Components import ElectronicComponents
from PIL import ImageFont, ImageDraw, Image
from Tools import CMD

class Micro(ElectronicComponents):
    def __init__(self, record_seconds_default=5, rate=44100, channels=1, key_stop=None, key_play_recoding=None, name=None):
        super().__init__(name=name, board=None, pin=0)
        self.record_seconds_default = record_seconds_default
        self.rate = rate
        self.channels = channels
        self.key_play_recoding = key_play_recoding
        self.key_stop = key_stop 
        self.rec_flag = True
          
    def getFrame(self):
        audio_data = None
        if not self.key_play_recoding is None:
            self.rec_flag = False
            CMD.clearCMD()
            print("Please press the key to record!")
            keyboard.wait(self.key_play_recoding)
            self.rec_flag = True
            
        if self.rec_flag:
            print("Recoding")
            audio_data = sd.rec(int(self.rate * self.record_seconds_default), samplerate=self.rate, channels=self.channels, dtype='float32')
            sd.wait()
            print("End recoding")
        return audio_data
        

    def getFrameToTensor(self, *args, **kwargs):
        frame = self.getFrame(*args, **kwargs)
        if frame is None: return None
        return tf.squeeze(tf.convert_to_tensor(frame))
    
    def playFrame(self, audio_data):
        sd.play(audio_data, self.rate)
        sd.wait()

class Camera(ElectronicComponents):
    def __init__(self, COM, resolution=[1280, 720], flip=False, key_stop='q', path_font=None, name=None):
        super().__init__(name=name, board=None, pin=0)
        self.COM = COM
        self.resolution = resolution
        self.flip = flip
        self.key_stop = key_stop
        self.path_font = path_font
        
        self.cap = cv2.VideoCapture(self.COM)
        if not self.cap.isOpened():
            raise RuntimeError("Camera error")
        else:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()
        
    def getFrame(self):
        ret, image = self.cap.read()
        if not ret: image = None
        elif self.flip: image = cv2.flip(image, 1)
        return image
    
    def liveView(self, frame):
        cv2.imshow("Camera", frame)
        stop = (cv2.waitKey(1) & 0xFF == ord(self.key_stop))
        return stop

    def writeText(self, frame, text, 
                  org=(0, 0),
                  color='red', size_text=35):
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame)
        font = ImageFont.truetype(self.path_font, size_text)
        draw = ImageDraw.Draw(pil_image)
        draw.text(org, text, font=font, fill=color)
        frame_add_text = np.asarray(pil_image)
        frame_add_text = cv2.cvtColor(frame_add_text, cv2.COLOR_RGB2BGR)
        return frame_add_text
         