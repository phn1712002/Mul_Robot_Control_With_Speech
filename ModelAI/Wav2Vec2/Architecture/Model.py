import os
import numpy as np
import tensorflow as tf
from Tools.Json import loadJson, saveJson
from keras import losses, optimizers, Model, Input
from keras.utils import pad_sequences
from transformers import TFWav2Vec2ForCTC, Wav2Vec2Processor, Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor

class CustomModel():
    def __init__(self, model:Model, loss=losses.mse, opt=optimizers.Adam()) -> None:
        self.model = model
        self.loss = loss
        self.opt = opt
        
    def predict(self, input):
        return None
    
    def build(self, summary=False):
        return self
    
    def getConfig(self):
        return {}
      
class Wav2Vec2(CustomModel):
    def __init__(self,
                 name='Wav2Vec2',
                 max_duration=1,
                 path_or_name_model='facebook/wav2vec2-base'):
        super().__init__(model=None, loss=None, opt=None)
        self.path_or_name_model = path_or_name_model
        self.name = name
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.path_or_name_model)
        self.tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(self.path_or_name_model)
        self.sampling_rate = self.feature_extractor.sampling_rate
        self.max_duration = max_duration
        self.processor = Wav2Vec2Processor(feature_extractor=self.feature_extractor, tokenizer=self.tokenizer)

    def formatInput(self, input):
        input_size = self.max_duration * self.sampling_rate
        if len(input) >= input_size:
            input = input[:input_size]
        else:
            num_pad = input_size - len(input)
            pad = np.zeros(shape=(num_pad, ))
            input = np.concatenate([input, pad], axis=0)
        input = self.encoderAudio(input=input)
        return input
    
    def encoderAudio(self, input):
        encoder = self.processor(input, sampling_rate=self.sampling_rate, return_tensors='tf', padding='longest')  
        return encoder.input_values
    
    def decoderText(self, output_tf):
        predicted_ids = tf.math.argmax(output_tf, axis=-1)
        transcription = self.processor.batch_decode(predicted_ids)
        return transcription
    
    def build(self, summary=False):
        input_size = self.sampling_rate * self.max_duration
        input_values = Input(shape=(input_size,), name='input_values')
            
        wav2vec2 = TFWav2Vec2ForCTC.from_pretrained(self.path_or_name_model, from_pt=True)
        output_values = wav2vec2(input_values)
        model = Model(inputs=input_values, outputs=output_values.logits, name=self.name)
        if summary:
            model.summary()
        self.model = model
        return self 
    
    def predict(self, input):
        input_tf = self.formatInput(input=input)
        output_tf = self.model.predict_on_batch(input_tf)
        output = self.decoderText(output_tf=output_tf)
        return output
    
    def getConfig(self):
        return {
            'name': self.name,
            'max_duration': self.max_duration
        }
    def exportTFLite(self, path_export='./Checkpoint/export/'):
        if os.path.exists(path_export):
            # Convert to tflite
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
            tflite_model = converter.convert()
            
            # Get config
            config_model = self.getConfig()
            
            # Save config
            path_tflite = path_export + self.name + '.tflite'
            path_json_config = path_export + self.name + '.json'
            
            self.feature_extractor.save_pretrained(path_export)
            self.tokenizer.save_pretrained(path_export)
            saveJson(path=path_json_config, data=config_model, encoding=None)
            tf.io.write_file(filename=path_tflite, contents=tflite_model)
        
            return Wav2Vec2_tflite(name_file=self.name, path=path_export).build()
        else: 
            return self
class Wav2Vec2_tflite(Wav2Vec2):
    def __init__(self, path='./Checkpoint/export/', name_file='Wav2Vec2'):
        
        self.name_file = name_file
        self.path = path
        
        self.index_input = None
        self.index_output = None
        self.dtype_input = None
        if os.path.exists(path):
            path_json_config = path + name_file + '.json'
            config_model = loadJson(path=path_json_config)
            super().__init__(path_or_name_model=path, **config_model)
        else:
            raise RuntimeError('Model load error')
          
    def build(self):
        self.model = tf.lite.Interpreter(model_path=self.path + self.name_file + '.tflite')
        self.index_input = self.model.get_input_details()[0]['index']
        self.dtype_input = self.model.get_input_details()[0]['dtype']
        self.index_output = self.model.get_output_details()[0]['index']
        return self
    
    def __invoke(self, input_tf):
        model = self.model 
        shape_input = (input_tf.shape[0], input_tf.shape[1])
        model.resize_tensor_input(self.index_input, shape_input)
        model.allocate_tensors()
        model.set_tensor(self.index_input, input_tf)
        model.invoke()
        output = model.get_tensor(self.index_output)
        tf_output = tf.convert_to_tensor(output)
        return tf_output
    
    def predict(self, input):
        input_tf = super().formatInput(input)
        output_tf = self.__invoke(input_tf)
        output = super().decoderText(output_tf)
        return output[0]