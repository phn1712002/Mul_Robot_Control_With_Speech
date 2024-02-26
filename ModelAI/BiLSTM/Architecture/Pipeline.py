import tensorflow as tf
import numpy as np
from .Model import NERBiLSTM
from keras.preprocessing.text import Tokenizer

class PipelineNERBiLSTM(NERBiLSTM):
    def __init__(self, tags_map: Tokenizer, vocab_map: Tokenizer, config_model=None):
        
        super().__init__(tags_map=tags_map, vocab_map=vocab_map, opt=None, loss=None, **config_model)
 
    def mapProcessing(self, seq, lable):
        seq = tf.py_function(super().encoderSeq, inp=[seq], Tout=tf.int32)
        lable = tf.py_function(super().encoderLable, inp=[lable], Tout=tf.int32)
        return (seq, lable)
    
    def __call__(self, dataset, batch_size):
        if not dataset is None:
            data = tf.data.Dataset.from_tensor_slices(dataset)
            data = (data.map(self.mapProcessing, num_parallel_calls=tf.data.AUTOTUNE)
                    .padded_batch(batch_size, padded_shapes=(tf.TensorShape([self.max_len, ]), tf.TensorShape([self.max_len, self.num_tags])))
                    .prefetch(buffer_size=tf.data.AUTOTUNE))
        else:
            data = None
        return data