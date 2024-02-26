import os
import tensorflow as tf
import numpy as np
from keras.utils import to_categorical, pad_sequences
from Tools.Json import loadJson, saveJson
from keras import optimizers, losses, Model, Input
from keras.preprocessing.text import Tokenizer
from keras.layers import LSTM, Embedding, Dense, Bidirectional, TimeDistributed, Dropout

class CustomModel():
    def __init__(self, vocab_map:Tokenizer, tags_map:Tokenizer, model=Model(), loss=losses.CategoricalCrossentropy(from_logits=True), opt=optimizers.Adam()):
        self.vocab_map = vocab_map
        self.tags_map = tags_map
        self.model = model
        self.loss = loss
        self.opt = opt
        
    def build(self, summary=False):
        pass
    
    def getConfig(self):
        pass
    
    def fit(self, train_dataset, dev_dataset=None, epochs=1, callbacks=None):
        pass
    
    def predict(self, input):
        pass
    
class NERBiLSTM(CustomModel):
    def __init__(self, 
                 vocab_map:Tokenizer,
                 tags_map:Tokenizer,
                 name="NERBiLSTM", 
                 max_len=50,
                 embedding_dim=20,
                 num_layers=1,
                 hidden_size=512,
                 rate_dropout=0.5,
                 decode='utf-8',
                 opt=optimizers.Adam(),
                 loss=losses.CategoricalCrossentropy(from_logits=True)):
        super().__init__(vocab_map=vocab_map, tags_map=tags_map, model=None, opt=opt, loss=loss)
        self.name = name
        self.max_len = max_len
        self.vocab_size = len(vocab_map.index_word) + 1
        self.embedding_dim = embedding_dim
        self.num_tags = len(tags_map.index_word) + 1
        self.num_layers = num_layers
        self.hidden_size= hidden_size
        self.rate_dropout = rate_dropout
        self.decode = decode

    def build(self, summary=False):
        strategy = tf.distribute.MirroredStrategy()
        with strategy.scope():
            input = Input(shape=(self.max_len, ), name="input")
            
            X = Embedding(input_dim=self.vocab_size, output_dim = self.embedding_dim, input_length = self.max_len, mask_zero=False, name="embdding")(input)
            X = Dropout(self.rate_dropout)(X)
            for i in range(1, self.num_layers + 1):
                X = Bidirectional(LSTM(units=self.hidden_size, return_sequences=True, recurrent_dropout=self.rate_dropout), name=f"Bidirectional_{i}")(X)
                
            X = LSTM(units=self.hidden_size * 2, return_sequences=True, recurrent_dropout=self.rate_dropout, name="LSTM")(X) 
            output = TimeDistributed(Dense(self.num_tags, activation = 'softmax'), name="TimeDistributed")(X)
        
            model = Model(inputs=input, outputs=output, name=self.name)
         
            model.compile(optimizer=self.opt, loss=self.loss, metrics=["accuracy"])
        if summary:
            model.summary()
            
        self.model = model
        return self
    
    def fit(self, train_dataset, dev_dataset=None, epochs=1, callbacks=None):
        
        self.model.fit(x=train_dataset,
                       validation_data=dev_dataset,
                       epochs=epochs,
                       callbacks=callbacks)
        return self
        
    def predict(self, input):
        
        input_tf = self.formatInput(input=input)
        output_tf = self.model.predict_on_batch(input_tf)
        output = self.decoderLable(output_tf)
        return  list(zip(input.split(), output.split()))
    
    def formatInput(self, input):
        input_size = len(input.split())
        input_split = input.split()
        list_tf = []
        if input_size > self.max_len + 1:
            for index in range(0, len(input_split) + 1 - self.max_len):
                begin = index
                end = begin + self.max_len
                input_join = ' '.join(input_split[begin:end])    
                input_tf = self.encoderSeq(tf.convert_to_tensor(input_join))
                list_tf.append(input_tf)
        else:
            input_tf = self.encoderSeq(tf.convert_to_tensor(input))
            list_tf.append(input_tf)
        return tf.convert_to_tensor(list_tf)
    
    
    def getConfig(self):
        return {
            "name": self.name,
            "max_len": self.max_len,
            "embedding_dim": self.embedding_dim,
            "num_layers": self.num_layers,
            "hidden_size": self.hidden_size,
            "rate_dropout": self.rate_dropout,
            "decode": self.decode
        }
        
    def encoderSeq(self, seq=None):
        
        seq = seq.numpy().decode(self.decode)
        seq = self.vocab_map.texts_to_sequences([seq])
        seq = tf.convert_to_tensor(seq)
        seq = pad_sequences(seq, value=0, maxlen=self.max_len, padding='post')
        seq = tf.squeeze(seq)
        return tf.cast(seq, dtype=tf.int32)
    
    def encoderLable(self, lable=None):
        
        lable = lable.numpy().decode(self.decode)
        lable = self.tags_map.texts_to_sequences([lable])
        lable = tf.convert_to_tensor(lable)
        lable = pad_sequences(lable, value=0, maxlen=self.max_len, padding='post')
        lable = tf.squeeze(lable)
        lable = [to_categorical(i, num_classes=self.num_tags, dtype='int32') for i in lable.numpy()]
        return tf.convert_to_tensor(lable, dtype=tf.int32)
    
    def decoderLable(self, output_tf=None):
                        
        if output_tf.shape[0] == 1:
            output_tf = tf.math.argmax(output_tf, axis=-1)
            output = tf.squeeze(output_tf).numpy()
            output = self.tags_map.sequences_to_texts([output])
        else:
            max_index = tf.math.argmax(output_tf, axis=-1)
            max_index = tf.squeeze(max_index).numpy() 
            
            max_prob = tf.math.reduce_max(output_tf, axis=-1)
            max_prob = tf.squeeze(max_prob).numpy() 
            
            max_index_join = None
            max_index_join = None
            for index in range(0, len(max_prob) - 1):
                
                if index == 0: 
                    max_index_join = max_index[index]
                    max_prob_join = max_prob[index]
                
                extended_matrix_1_prob = np.append(max_prob_join, 0)
                extended_matrix_1_index = np.append(max_index_join, 0)
                
                num_value_insert = index + 1
                value_to_insert = np.zeros(num_value_insert)
                extended_matrix_2_prob = np.insert(max_prob[index + 1], 0, value_to_insert)
                extended_matrix_2_index = np.insert(max_index[index + 1], 0, value_to_insert)
                
                max_prob_join = np.max(np.vstack((extended_matrix_1_prob, extended_matrix_2_prob)), axis=0)
                max_index_join = []
                for i in range(0, len(max_prob_join)):
                    if max_prob_join[i] == extended_matrix_1_prob[i]: max_index_join.append(extended_matrix_1_index[i])
                    else: max_index_join.append(extended_matrix_2_index[i])
                            
            output = self.tags_map.sequences_to_texts([max_index_join])
        return output[0]
    
    def decoderSeq(self, input_tf=None):
        
        input = tf.squeeze(input_tf).numpy()
        input = self.vocab_map.sequences_to_texts([input])
        return input
    
    def exportTFlite(self, path_export):
        if os.path.exists(path_export):
            # Convert to tflite
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            #converter.optimizations = [tf.lite.Optimize.DEFAULT]
            #onverter.experimental_new_converter=True
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
            tflite_model = converter.convert()
            
            # Get config model
            config_model = self.getConfig()
            config_vocab = self.vocab_map.to_json()
            config_tags = self.tags_map.to_json()
            
            # Path config
            path_tflite = path_export + self.name + '.tflite' 
            path_json_vocab = path_export + self.name + '_vocab.json'
            path_json_tag = path_export + self.name + '_tags.json'
            path_json_config = path_export + self.name + '.json'
            
            # Save
            saveJson(path=path_json_config, data=config_model)
            saveJson(path=path_json_vocab, data=config_vocab, encoding=None)  
            saveJson(path=path_json_tag, data=config_tags, encoding=None) 
            tf.io.write_file(filename=path_tflite, contents=tflite_model)
            
            print(f"Export model to tflite filename:{path_tflite} and json:{path_json_config}")
        else:
            raise RuntimeError('Error path')
    
class NERBiLSTM_tflite(NERBiLSTM):
    def __init__(self, name_file='NER_BiLSTM', path='./Checkpoint/export/'):
        
        self.name_file = name_file
        self.path = path
        
        self.index_input = None
        self.index_ouput = None
        self.dtype_input = None
        
        if os.path.exists(path):
            path_json_vocab = path + name_file + '_vocab.json'
            path_json_tag = path + name_file + '_tags.json'
            path_json_config = path + name_file + '.json'
            
            config_model = loadJson(path=path_json_config)
            config_vocab = loadJson(path=path_json_vocab, encoding=None)
            config_tags = loadJson(path=path_json_tag, encoding=None)
            vocab_map = tf.keras.preprocessing.text.tokenizer_from_json(config_vocab)
            tags_map = tf.keras.preprocessing.text.tokenizer_from_json(config_tags)
            super().__init__(vocab_map=vocab_map, tags_map=tags_map, **config_model)
        else:
            raise RuntimeError('Model load error')
            
    def build(self):
        self.model = tf.lite.Interpreter(model_path=self.path + self.name_file + '.tflite')
        self.index_input = self.model.get_input_details()[0]['index']
        self.dtype_input = self.model.get_input_details()[0]['dtype']
        self.index_ouput = self.model.get_output_details()[0]['index']
        return self
    
    def predict(self, input):
        input_tf = super().formatInput(input)
        output_tf  = self.__invoke(input_tf)
        output = super().decoderLable(output_tf)
        return list(zip(input.split(), output.split()))
    
    def __invoke(self, input_tf):
        model = self.model
        shape_input = (input_tf.shape[0], input_tf.shape[1])
        model.resize_tensor_input(self.index_input, shape_input)
        model.allocate_tensors()
        model.set_tensor(self.index_input, tf.cast(input_tf, dtype=self.dtype_input))
        model.invoke()
        ouput = model.get_tensor(self.index_ouput)
        tf_output = tf.convert_to_tensor(ouput)
        return tf_output