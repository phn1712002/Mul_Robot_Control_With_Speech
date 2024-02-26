import keras, os
import tensorflow as tf
from keras import losses, optimizers
from Tools.Json import loadJson
from .Layers import AudioClipLayer, InterpolationLayer, CropLayer, IndependentOutputLayer, DiffOutputLayer, Squeeze, ExpandDims, Decimate, BilinearInterpol


class CustomModel():
    def __init__(self, model=keras.Model(), opt=optimizers.Adam(), loss=losses.mse):
        self.model = model
        self.opt = opt
        self.loss = loss
    def fit(self):
        pass
    def build(self):
        pass
    def getConfig(self):
        pass
    def predict(self):
        pass
    
class WaveUnet(CustomModel):
    def __init__(self,
               name='WaveUnet',
               num_initial_filters = 24, num_layers = 12, kernel_size = 15, merge_filter_size = 5,
               source_names = ['speech', 'noise'], num_channels = 1, output_filter_size = 1,
               padding = 'same', input_size = 16384 * 3, context = False, upsampling_type = 'learned',
               output_activation = 'linear', output_type = 'difference', 
               loss=losses.mse, opt=optimizers.Adam(),
               sr=16000):
        super().__init__(model=None, opt=opt, loss=loss)
        self.name = name
        self.num_initial_filters = num_initial_filters
        self.num_layers = num_layers
        self.kernel_size = kernel_size
        self.merge_filter_size = merge_filter_size
        self.source_names = source_names
        self.num_channels = num_channels
        self.output_filter_size = output_filter_size
        self.padding = padding
        self.input_size = input_size
        self.context = context
        self.upsampling_type = upsampling_type
        self.output_activation = output_activation
        self.output_type = output_type
        self.sr = sr
        
    def build(self, summary=False):
        strategy = tf.distribute.MirroredStrategy()
        with strategy.scope():
            enc_outputs = []
            
            raw_input = keras.layers.Input(shape=(self.input_size, self.num_channels),name='raw_input')
            X = raw_input
            inp = raw_input
            
            for i in range(self.num_layers):
                X = keras.layers.Conv1D(filters=self.num_initial_filters + (self.num_initial_filters * i),
                                        kernel_size=self.kernel_size,strides=1,
                                        padding=self.padding, name='Down_Conv_'+str(i))(X)
                X = keras.layers.LeakyReLU(name='Down_Conv_Activ_'+str(i))(X)

                enc_outputs.append(X)

                X = Decimate(name='Decimate_'+str(i))(X)
            
            X = keras.layers.Conv1D(filters=self.num_initial_filters + (self.num_initial_filters * self.num_layers),
                                    kernel_size=self.kernel_size,strides=1,
                                    padding=self.padding, name='Down_Conv_'+str(self.num_layers))(X)
            X = keras.layers.LeakyReLU(name='Down_Conv_Activ_'+str(self.num_layers))(X)

            for i in range(self.num_layers):
                X = ExpandDims(name='exp_dims_'+str(i))(X)
        
                if self.upsampling_type == 'learned':
                    X = InterpolationLayer(name='IntPol_'+str(i), padding=self.padding)(X)
                else:
                    X = BilinearInterpol(context=self.context, name='bilinear_interpol_'+str(i))(X)

                X = Squeeze(name='sq_dims_'+str(i))(X)
        
                c_layer = CropLayer(X, False, name='crop_layer_'+str(i))(enc_outputs[-i-1])
                X = keras.layers.Concatenate(axis=2, name='concatenate_'+str(i))([X, c_layer]) 


                X = keras.layers.Conv1D(filters=self.num_initial_filters + (self.num_initial_filters * (self.num_layers - i - 1)),
                                        kernel_size=self.merge_filter_size,strides=1,
                                        padding=self.padding, name='Up_Conv_'+str(i))(X)
                X = keras.layers.LeakyReLU(name='Up_Conv_Activ_'+str(i))(X)
                
            c_layer = CropLayer(X, False, name='crop_layer_'+str(self.num_layers))(inp)
            X = keras.layers.Concatenate(axis=2, name='concatenate_'+str(self.num_layers))([X, c_layer]) 
            X = AudioClipLayer(name='audio_clip_'+str(0))(X)

            if self.output_type == 'direct':
                X = IndependentOutputLayer(self.source_names, self.num_channels, self.output_filter_size, padding=self.padding, name='independent_out')(X)
            else:
                cropped_input = CropLayer(X, False, name='crop_layer_'+str(self.num_layers+1))(inp)
                X = DiffOutputLayer(self.source_names, self.num_channels, self.output_filter_size, padding=self.padding, name='diff_out')([X, cropped_input])
            
            o = X
            model = keras.Model(inputs=raw_input, outputs=o, name=self.name)
            
            # Setting Opt and Loss
            model.compile(optimizer=self.opt, loss=self.loss)
            
            # Show output model
            if summary:
                model.summary()
                data = model.output
                print('-' * 100)
                for key in data:
                    value = data[key]
                    print(f'Key: {key}, Type: {type(value)}, Shape: {value.shape}')
            self.model = model
            return self
        
    def fit(self, train_dataset, dev_dataset, epochs=1, callbacks=None):
        self.model.fit(train_dataset,
                       validation_data=dev_dataset,
                       epochs=epochs,
                       callbacks=callbacks
                       )
        return self
        
    def predict(self, audio_input):
        tf_audio_input = tf.convert_to_tensor(audio_input, dtype=tf.float32)
        tf_audio_input = tf.squeeze(tf_audio_input)
        tf_audio_input, excess_amount = self.cutAudio(tf_audio_input, 
                                                      win_lenght=self.input_size)
        tf_audio_output = self.model.predict_on_batch(tf_audio_input)
        audio_output = self.joinAudio(tf_audio_output['speech'],
                                      excess_amount=excess_amount)
        return audio_output
    
    def cutAudio(self, tf_signal, win_lenght):
        excess_amount = 0
        if len(tf_signal) ==  win_lenght:
            audio = tf_signal[tf.newaxis, :]
        else:
            if not len(tf_signal) <  win_lenght:
                for begin in range(0, len(tf_signal), win_lenght):
                    end = begin + win_lenght
                    if begin == 0:
                        audio = tf_signal[begin:end]
                    else:
                        audio_join = tf_signal[begin:end]
                        if not len(audio_join) == win_lenght:
                            excess_amount = win_lenght - len(audio_join)
                            audio_empty = tf.zeros(shape=(excess_amount,))
                            audio_join = tf.concat([audio_join, audio_empty], axis=0)
                        if begin == win_lenght:
                            audio = tf.stack((audio, audio_join), axis=0)
                        else:
                            audio_join = audio_join[tf.newaxis, :]
                            audio = tf.concat((audio, audio_join), axis=0)
            else:
                excess_amount = win_lenght - len(tf_signal)
                audio_empty = tf.zeros(shape=(excess_amount,))
                audio = tf.concat([tf_signal, audio_empty], axis=0)
                audio = audio[tf.newaxis, :]
        audio = tf.expand_dims(audio, axis=2)
        return tf.convert_to_tensor(audio, dtype=tf.float32), excess_amount
    
    def joinAudio(self, tf_audio_output, excess_amount=0):
        for index in range(0, len(tf_audio_output)):
            if index == 0:
                result = tf.squeeze(tf_audio_output[index])
            else:
                result = tf.concat([result, tf.squeeze(tf_audio_output[index])], axis=0)
        return result[0:result.shape[0]-excess_amount]
    
    def getConfig(self):
        return {
            'name': self.name,
            'num_initial_filters': self.num_initial_filters,
            'num_layers': self.num_layers,
            'kernel_size': self.kernel_size,
            'merge_filter_size': self.merge_filter_size,
            'source_names': self.source_names,
            'num_channels': self.num_channels,
            'output_filter_size': self.output_filter_size,
            'padding': self.padding,
            'input_size': self.input_size,
            'context': self.context,
            'upsampling_type': self.upsampling_type,
            'output_activation': self.output_activation,
            'output_type': self.output_type,
            'sr': self.sr,
        }

class WaveUnet_tflite(WaveUnet):
    def __init__(self, path='./Checkpoint/export/', name_file='WaveUnet'):

        self.path = path
        self.name_file = name_file
        
        self.index_input = None
        self.index_ouput = None
        self.dtype_input = None
        
        if os.path.exists(path):
            config_model = loadJson(path=path + name_file + '.json')
            super().__init__(**config_model)
        else:
            raise RuntimeError('Model load error')

    def predict(self, audio_input):
        tf_audio_input, excess_amount = super().cutAudio(tf_signal=audio_input, 
                                                           win_lenght=self.input_size)
        tf_audio_output = self.__invoke(tf_audio_input)
        audio_output = super().joinAudio(tf_audio_output=tf_audio_output,
                                           excess_amount=excess_amount)
        return audio_output
    
    def build(self):
        self.model = tf.lite.Interpreter(model_path=self.path + self.name_file + '.tflite')
        self.index_input = self.model.get_input_details()[0]['index']
        self.index_ouput = self.model.get_output_details()[1]['index']
        return self
    
    def close(self):
        self.model = None
        return self
    
    def __invoke(self, input_tf):
        model = self.model 
        shape_input = (input_tf.shape[0], input_tf.shape[1], input_tf.shape[2])
        model.resize_tensor_input(self.index_input, shape_input)
        model.allocate_tensors()
        model.set_tensor(self.index_input, input_tf)
        model.invoke()
        ouput = model.get_tensor(self.index_ouput)
        tf_output = tf.convert_to_tensor(ouput)
        return tf_output