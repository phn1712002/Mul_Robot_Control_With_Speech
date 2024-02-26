import tensorflow as tf
import numpy as np
from keras.layers import Layer


'''# Custom layers'''
class AudioClipLayer(Layer):
    def __init__(self, name=None, **kwargs):
        '''Initializes the instance attributes'''
        super().__init__(name=name, **kwargs)

    def build(self, input_shape):
        '''Create the state of the layer (weights)'''
        # initialize the weights
        pass
        
    def call(self, inputs, training):
        '''Defines the computation from inputs to outputs'''
        if training:
            return inputs
        else:
            return tf.maximum(tf.minimum(inputs, 1.0), -1.0)

    def get_config(self):
        config = super().get_config()
        return config
  
# Learned Interpolation layer
class InterpolationLayer(Layer):
    def __init__(self, padding = 'valid', name=None, **kwargs):
        '''Initializes the instance attributes'''
        super().__init__(name=name, **kwargs)
        self.padding = padding

    def build(self, input_shape):
        '''Create the state of the layer (weights)'''
        self.features = input_shape.as_list()[3]

        # initialize the weights
        w_init = tf.random_normal_initializer()
        self.w = tf.Variable(name='kernel',
            initial_value=w_init(shape=(self.features, ),
                                 dtype='float32'),
            trainable=True)

    def call(self, inputs):
        '''Defines the computation from inputs to outputs'''

        w_scaled = tf.math.sigmoid(self.w)

        counter_w = 1 - w_scaled

        conv_weights = tf.expand_dims(tf.concat([tf.expand_dims(tf.linalg.diag(w_scaled), axis=0), tf.expand_dims(tf.linalg.diag(counter_w), axis=0)], axis=0), axis=0)

        intermediate_vals = tf.nn.conv2d(inputs, conv_weights, strides=[1,1,1,1], padding=self.padding.upper())

        intermediate_vals = tf.transpose(intermediate_vals, [2, 0, 1, 3])
        out = tf.transpose(inputs, [2, 0, 1, 3])
        
        num_entries = out.shape.as_list()[0]
        out = tf.concat([out, intermediate_vals], axis=0)

        indices = list()

        # num_outputs = 2*num_entries - 1
        num_outputs = (2*num_entries - 1) if self.padding == 'valid' else 2*num_entries

        for idx in range(num_outputs):
            if idx % 2 == 0:
                indices.append(idx // 2)
            else:
                indices.append(num_entries + idx//2)
        out = tf.gather(out, indices)
        current_layer = tf.transpose(out, [1, 2, 0, 3])

        return current_layer
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'padding': self.padding,
            })
        return config 

class CropLayer(Layer):
    def __init__(self, x2, match_feature_dim=True, name=None, **kwargs):
        '''Initializes the instance attributes'''
        super().__init__(name=name, **kwargs)
        
        self.match_feature_dim = match_feature_dim
        if x2 is None: self.shape_x2 = x2.shape.as_list()
        else: self.shape_x2 = None

    def build(self, input_shape):
        '''Create the state of the layer (weights)'''
        # initialize the weights
        pass
        
    def call(self, inputs):
        '''Defines the computation from inputs to outputs'''
        if self.shape_x2 is None:
            return inputs
        
        def crop(tensor, target_shape, match_feature_dim=True):
            '''
            Crops a 3D tensor [batch_size, width, channels] along the width axes to a target shape.
            Performs a centre crop. If the dimension difference is uneven, crop last dimensions first.
            :param tensor: 4D tensor [batch_size, width, height, channels] that should be cropped. 
            :param target_shape: Target shape (4D tensor) that the tensor should be cropped to
            :return: Cropped tensor
            '''
            shape = np.array(tensor.shape.as_list())

            ddif = shape[1] - target_shape[1]

            if (ddif % 2 != 0):
                print('WARNING: Cropping with uneven number of extra entries on one side')
            # assert diff[1] >= 0 # Only positive difference allowed
            if ddif == 0:
                return tensor
            crop_start = ddif // 2
            crop_end = ddif - crop_start

            return tensor[:,crop_start:-crop_end,:]
        inputs = crop(inputs, self.shape_x2, self.match_feature_dim)
        return inputs
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'match_feature_dim': self.match_feature_dim,
            'shape_x2': self.shape_x2
        })
        return config
    
class IndependentOutputLayer(Layer):
    def __init__(self, source_names, num_channels, filter_width, padding='valid', name=None, **kwargs):
        '''Initializes the instance attributes'''
        super().__init__(name=name, **kwargs)
        self.source_names = source_names
        self.num_channels = num_channels
        self.filter_width = filter_width
        self.padding = padding

        self.conv1a = tf.keras.layers.Conv1D(self.num_channels, self.filter_width, padding= self.padding)

    def build(self, input_shape):
        '''Create the state of the layer (weights)'''
        pass
        
    def call(self, inputs, training):
        '''Defines the computation from inputs to outputs'''
        outputs = {}
        for name in self.source_names:
            out = self.conv1a(inputs)
            outputs[name] = out
        
        return outputs
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'source_names': self.source_names,
            'num_channels': self.num_channels,
            'filter_width': self.filter_width,
            'padding': self.padding,
            })
        return config

class DiffOutputLayer(Layer):
    def __init__(self, source_names, num_channels, filter_width, padding='valid', name=None, **kwargs):
        '''Initializes the instance attributes'''
        super().__init__(name=name, **kwargs)
        self.source_names = source_names
        self.num_channels = num_channels
        self.filter_width = filter_width
        self.padding = padding

        self.conv1a = tf.keras.layers.Conv1D(self.num_channels, self.filter_width, padding=self.padding)

    def build(self, input_shape):
        '''Create the state of the layer (weights)'''
        pass
        
    def call(self, inputs, training):
        '''Defines the computation from inputs to outputs'''
        outputs = {}
        sum_source = 0
        for name in self.source_names[:-1]:
            out = self.conv1a(inputs[0])
            out = AudioClipLayer()(out)
            outputs[name] = out
            sum_source = sum_source + out
        
        last_source = CropLayer(sum_source)(inputs[1]) - sum_source
        last_source = AudioClipLayer()(last_source)

        outputs[self.source_names[-1]] = last_source

        return outputs
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'source_names': self.source_names,
            'num_channels': self.num_channels,
            'filter_width': self.filter_width,
            'padding': self.padding,
            })
        return config

class Squeeze(Layer):
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        
    def build(self, input_shape):
        pass
    
    def call(self, inputs, *args, **kwargs):
        output = tf.squeeze(inputs, axis=1)
        return output
    
    def get_config(self):
        return super().get_config()

class ExpandDims(Layer):
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        
    def build(self, input_shape):
        pass
    
    def call(self, inputs, *args, **kwargs):
        output = tf.expand_dims(inputs, axis=1)
        return output
    
    def get_config(self):
        return super().get_config()

class Decimate(Layer):
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        
    def build(self, input_shape):
        pass
    
    def call(self, inputs, *args, **kwargs):
        return inputs[:,::2,:]
    
    def get_config(self):
        return super().get_config()

class BilinearInterpol(Layer):
    def __init__(self, context=True, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.context = context
    
    def build(self, input_shape):
        pass
    
    def call(self, inputs, *args, **kwargs):
        if self.context:
            ouput = tf.image.resize(inputs, [1, inputs.shape.as_list()[2] * 2 - 1])
        else:
            ouput = tf.image.resize(inputs, [1, inputs.shape.as_list()[2] * 2])
        return ouput
    
    def get_config(self):
        config = super().get_config()
        config.update({'context': self.context})
        return config