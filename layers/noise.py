from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from .base import BaseLayer

		
__all__ = [
	"DropoutLayer",
	"GaussianNoiseLayer",
	"VariationalSampleLayer",
	"CategoricalSampleLayer",
]


class DropoutLayer(BaseLayer):
	def __init__(self, incoming, keep_prob=0.5, **kwargs):
				
		self.incoming_shape = incoming.get_output_shape()
		self.incoming = incoming
		self.keep_prob = keep_prob
		self.output_shape = self.incoming_shape
		
	def get_input_shape(self):
		return self.incoming_shape
	
	def get_output(self):
		return tf.nn.dropout(self.incoming.get_output(), keep_prob=self.keep_prob)
	
	def get_output_shape(self):
		return self.output_shape


class GaussianNoiseLayer(BaseLayer):
	def __init__(self, incoming, mu=0.0, sigma=0.1, **kwargs):
				
		self.incoming_shape = incoming.get_output_shape()
		self.incoming = incoming
		self.output_shape = self.incoming_shape	
		self.mu = mu
		self.sigma = sigma

		
	def get_input_shape(self):
		return self.incoming_shape
	
	def get_output(self):
		noise = tf.random_normal(shape=self.incoming_shape, mean=self.mu, stddev=self.sigma, dtype=tf.float32) 
		return self.incoming.get_output() + noise
	
	def get_output_shape(self):
		return self.output_shape
		
		
class VariationalSampleLayer(BaseLayer):
	def __init__(self, incoming_mu, incoming_logvar, **kwargs):
				
		self.incoming_mu = incoming_mu.get_output()
		self.incoming_sigma = tf.sqrt(tf.exp(incoming_logvar.get_output())+1e-7)
		self.incoming_shape = incoming_mu.get_output_shape()
		self.output_shape = self.incoming_shape		
		
	def get_input_shape(self):
		return self.incoming_shape
	
	def get_output(self):
		z = tf.random_normal(shape=tf.shape(self.incoming_mu), mean=0.0, stddev=1.0, dtype=tf.float32) 
		return self.incoming_mu + tf.multiply(self.incoming_sigma, z)

	def get_output_shape(self):
		return self.output_shape
		





def gumbel_softmax_sample(logits, temperature): 
	""" Draw a sample from the Gumbel-Softmax distribution"""
	
	def sample_gumbel(shape, eps=1e-20): 
		"""Sample from Gumbel(0, 1)"""
		U = tf.random_uniform(shape,minval=0,maxval=1)
		return -tf.log(-tf.log(U + eps) + eps)
	
	y = logits + sample_gumbel(tf.shape(logits))
	return tf.nn.softmax( y / temperature)



class CategoricalSampleLayer(BaseLayer):
	def __init__(self, incoming, temperature, hard=False, **kwargs):
				
		shape = incoming.get_output_shape().as_list()
		num_classes = shape[2]
		num_categories = shape[1]

		self.incoming_shape = incoming.get_output_shape()
		self.output_shape = self.incoming_shape	
		self.temperature = temperature	
		self.hard = hard

		#softmax = tf.nn.softmax(incoming.get_output(), dim=-1)
		#self.output = 

		reshape = tf.reshape(incoming.get_output(), [-1, num_classes], **kwargs)
		softmax = gumbel_softmax_sample(reshape, temperature)

		if self.hard:
			k = tf.shape(softmax)[-1]
			#y_hard = tf.cast(tf.one_hot(tf.argmax(y,1),k), y.dtype)
			y_hard = tf.cast(tf.equal(softmax, tf.reduce_max(softmax, 1, keep_dims=True)), softmax.dtype)
			softmax = tf.stop_gradient(y_hard - softmax) + softmax

		self.output = tf.reshape(softmax, [-1, num_categories, num_classes])
		
	def get_input_shape(self):
		return self.incoming_shape
	
	def get_output(self):
		return self.output

	def get_output_shape(self):
		return self.output_shape
		