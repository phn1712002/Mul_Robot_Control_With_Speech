
import cv2, keyboard, numpy as np, sounddevice as sd
from .Components import ElectronicComponents


class Micro(ElectronicComponents):
    def __init__(self, record_seconds_default=5, rate=44100, channels=1, name=None):
        super().__init__(name=name, board=None, pin=0)
        self.record_seconds_default = record_seconds_default
        self.rate = rate
        self.channels = channels
        
    def getFrame(self, record_seconds=None, key_play_recoding=lambda: keyboard.wait('enter')):
        if not key_play_recoding is None:
            print("Please press the key to record!")
            key_play_recoding()
        
        duration = 0
        if not record_seconds is None: duration = record_seconds
        else: duration = self.record_seconds_default
        print("Recoding")
        audio_data = sd.rec(int(self.rate * duration), samplerate=self.rate, channels=self.channels, dtype='float32')
        sd.wait()
        print("End recoding")
        return audio_data
    
    def playFrame(self, audio_data):
        sd.play(audio_data, self.rate)
        sd.wait()

class Camera(ElectronicComponents):
    def __init__(self, COM, resolution=[1280, 720], flip=False, name=None):
        super().__init__(name=name, board=None, pin=0)
        self.COM = COM
        self.resolution = resolution
        self.flip = flip

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
         