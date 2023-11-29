import tensorflow as tf
import time
"""
We employ a residual connection around each of the two sub-layers, followed by layer normalization.
That is, the output of each sub-layer is LayerNorm(x+ Sublayer(x)), where Sublayer(x) is the function implemented by the sub-layer itself. """
class LayerNormResidualConnection(object):
    def __init__(self,x,y,layer_index,residual_dropout=0.1,use_residual_conn=True):
        self.x=x
        self.y=y
        self.layer_index=layer_index
        self.residual_dropout=residual_dropout
        #print("LayerNormResidualConnection.residual_dropout:",self.residual_dropout)
        self.use_residual_conn=use_residual_conn

    #call residual connection and layer normalization
    def layer_norm_residual_connection(self):
        if not self.use_residual_conn:
            return self.layer_normalization(self.x)
        x_residual=self.residual_connection()
        return self.layer_normalization(x_residual)

    def residual_connection(self):
        return self.x + tf.nn.dropout(self.y, 1.0 - self.residual_dropout)

    # layer normalize the tensor x, averaging over the last dimension.
    def layer_normalization(self,x):
        """
        x should be:[batch_size,sequence_length,d_model]
        :return:
        """
        filter=x.get_shape()[-1] #last dimension of x. e.g. 512
        #print("layer_normalization:==================>variable_scope:","layer_normalization"+str(self.layer_index))
        with tf.variable_scope(f"layer_normalization{str(self.layer_index)}"):
            # 1. normalize input by using  mean and variance according to last dimension
            mean=tf.reduce_mean(x,axis=-1,keepdims=True) #[batch_size,sequence_length,1]
            variance=tf.reduce_mean(tf.square(x-mean),axis=-1,keepdims=True) #[batch_size,sequence_length,1]
            norm_x=(x-mean)*tf.rsqrt(variance+1e-6) #[batch_size,sequence_length,d_model]
            # 2. re-scale normalized input back
            scale=tf.get_variable("layer_norm_scale",[filter],initializer=tf.ones_initializer) #[filter]
            bias=tf.get_variable("layer_norm_bias",[filter],initializer=tf.ones_initializer) #[filter]
            return norm_x*scale+bias

def test():
    start = time.time()

    batch_size=128
    sequence_length=1000
    d_model=512
    x=tf.ones((batch_size,sequence_length,d_model))
    y=x*3-0.5
    layer_norm_residual_conn=LayerNormResidualConnection(x,y,0,'encoder')
    output=layer_norm_residual_conn.layer_norm_residual_connection()

    end = time.time()
    print("x:",x,";y:",y)
    print("output:",output,";time spent:",(end-start))

#test()