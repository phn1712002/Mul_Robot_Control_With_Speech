import tensorflow as tf
import librosa
import numpy as np
from audiomentations import AddGaussianSNR, AddBackgroundNoise
from .Model import WaveUnet
from keras import Model


class PipelineWaveUnet(WaveUnet):
    def __init__(self, params_noise=None, config_model=None,**kwargs):
        super().__init__(opt=None, loss=None, **config_model)
        self.params_noise = params_noise
    
    def predictInCallbacks(self, model: Model, audio_input=None):
        tf_audio_input = tf.convert_to_tensor(audio_input, dtype=tf.float32)
        tf_audio_input = tf.squeeze(tf_audio_input)
        tf_audio_input, excess_amount = super().cutAudio(tf_audio_input, 
                                                      win_lenght=self.input_size)
        tf_audio_output = model.predict_on_batch(tf_audio_input)
        audio_output = super().joinAudio(tf_audio_output['speech'],
                                      excess_amount=excess_amount)
        return audio_output
    
    def augmentationAudio(self, audio):
        transform = AddBackgroundNoise(**self.params_noise['AddBackgroundNoise'])
        audio_noise = transform(samples=audio, sample_rate=self.sr)
        noise = audio_noise - audio 
            
        transform = AddGaussianSNR(**self.params_noise['AddGaussianSNR'])
        audio_noise = transform(samples=audio_noise, sample_rate=self.sr)
        noise = audio_noise - audio 
            
            
        result = np.stack((audio_noise, noise), axis=1)
        return tf.convert_to_tensor(result, dtype=tf.float32)
    
    def loadAudio(self, path):
        audio, _ = librosa.load(path, sr=self.sr, mono=True)
        len_audio = len(audio)

        if len_audio > self.input_size:
            begin = np.random.randint(low=0, high=len_audio - self.input_size - 1)
            end = begin + self.input_size
            audio = audio[begin:end]
        else:
            audio_empty = np.zeros(shape=(self.input_size - len_audio,), dtype=float)
            audio = np.concatenate([audio.astype(float), audio_empty], dtype=float)
        return tf.convert_to_tensor(audio, dtype=tf.float32)
    
    def mapProcessing(self, path):
        audio_ouput = tf.numpy_function(func=self.loadAudio, inp=[path], Tout=tf.float32)
        
        audio_nosie = tf.numpy_function(func=self.augmentationAudio, inp=[audio_ouput], Tout=tf.float32)
        audio_input, noise = tf.split(audio_nosie, 2, axis=1)
        audio_ouput = tf.reshape(audio_ouput, (-1, 1))
        
        output_audio_list = [audio_ouput, noise]
        output = {}
        for index in range(0, len(self.source_names)):
            output[self.source_names[index]] = output_audio_list[index]
        return audio_input, output
    
    def __call__(self, dataset=None, batch_size=1):
        data = tf.data.Dataset.from_tensor_slices(dataset)
        padded_shapes_output = {key: tf.TensorShape([self.input_size, 1]) for key in self.source_names}
        data = (data.map(self.mapProcessing, num_parallel_calls=tf.data.AUTOTUNE)
                .padded_batch(batch_size, padded_shapes=(tf.TensorShape([self.input_size, 1]), padded_shapes_output))
                .prefetch(buffer_size=tf.data.AUTOTUNE))
        return data