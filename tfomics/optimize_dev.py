import tensorflow as tf


__all__ = [
	"build_updates",
	"build_loss",
	"cost_function"
]


def build_updates(optimization):

	if 'optimizer' in optimization.keys():
		optimizer = optimization['optimizer']
	else:
		optimizer = 'adam'
		optimization['learning_rate'] = 0.001

	if optimizer == 'sgd':
		learning_rate = 0.005
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'adadelta'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.GradientDescentOptimizer(learning_rate=learning_rate, 
												 use_locking=use_locking, 
												 name=name)

	elif optimizer == 'momentum':
		learning_rate = 0.005
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		momentum = 0.9
		if 'momentum' in optimization.keys():
			momentum = optimization['momentum']
		use_nesterov = True
		if 'use_nesterov' in optimization.keys():
			use_nesterov = optimization['use_nesterov']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'momenum'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.MomentumOptimizer(learning_rate=learning_rate, 
										  momentum=momentum, 
										  use_nesterov=use_nesterov, 
										  use_locking=use_locking, 
										  name=name)
	
	elif optimizer == 'adam':
		learning_rate = 0.001
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		beta1 = 0.95
		if 'beta1' in optimization.keys():
			beta1 = optimization['beta1']
		beta2 = 0.999
		if 'beta2' in optimization.keys():
			beta2 = optimization['beta2']
		epsilon = 1e-08
		if 'epsilon' in optimization.keys():
			epsilon = optimization['epsilon']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'adam'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.AdamOptimizer(learning_rate=learning_rate, 
									  beta1=beta1, 
									  beta2=beta2, 
									  epsilon=epsilon, 
									  use_locking=use_locking, 
									  name=name)

	elif optimizer == 'rmsprop':
		learning_rate = 0.001
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		rho = 0.95
		if 'rho' in optimization.keys():
			rho = optimization['rho']
		epsilon = 1e-08
		if 'epsilon' in optimization.keys():
			epsilon = optimization['epsilon']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'rmsprop'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.RMSPropOptimizer(learning_rate=learning_rate, 
										 rho=rho, 
										 epsilon=epsilon, 
										 use_locking=use_locking, 
										 name=name)
	
	elif optimizer == 'adadelta':
		learning_rate = 0.001
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		rho = 0.95
		if 'rho' in optimization.keys():
			rho = optimization['rho']
		epsilon = 1e-08
		if 'epsilon' in optimization.keys():
			epsilon = optimization['epsilon']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'adadelta'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.AdadeltaOptimizer(learning_rate=learning_rate, 
										  rho=rho, 
										  epsilon=epsilon, 
										  use_locking=use_locking, 
										  name=name)

	elif optimizer == 'adagrad':
		learning_rate = 0.001
		if 'learning_rate' in optimization.keys():
			leanring_rate = optimization['learning_rate']
		initial_accumulator_value = 0.95
		if 'initial_accumulator_value' in optimization.keys():
			initial_accumulator_value = optimization['initial_accumulator_value']
		use_locking = False
		if 'use_locking' in optimization.keys():
			use_locking = optimization['use_locking']
		name = 'adagrad'
		if 'name' in optimization.keys():
			name = optimization['name']
		return tf.train.AdagradOptimizer(learning_rate=learning_rate, 
										 initial_accumulator_value=initial_accumulator_value, 
										 use_locking=use_locking, 
										 name=name)




def build_loss(network, placeholders, optimization):
	

	if optimization['objective'] == 'lower_bound':
		if 'binary' in optimization:
			binary = optimization['binary']
		else:
			binary = False

		loss, predictions = variational_lower_bound(network, placeholders['inputs'], binary=binary)

	else:
		predictions = network['output'].get_output()

		# cost function
		if (optimization['objective'] == 'binary') | (optimization['objective'] == 'categorical'):
			clip_value = True
		else:
			if 'clip_value' in optimization.keys():
				clip_value = optimization['clip_value']
			else:
				clip_value = False

		# build loss function
		loss = cost_function(predictions=predictions, targets=placeholders['targets'], 
							 objective=optimization['objective'], 
							 clip_value=clip_value)


	if 'l1' in optimization.keys():
		l1 = get_l1_parameters(network)
		loss += tf.reduce_sum(tf.abs(l1)) * optimization['l1']

	if 'l2' in optimization.keys():
		l2 = get_l1_parameters(network)
		loss += tf.reduce_sum(tf.square(l2)) * optimization['l2']

	return loss, predictions


def variational_lower_bound(network, targets, deterministic=False, binary=True):

	z_mu = network['encode_mu'].get_output()
	z_logsigma = network['encode_logsigma'].get_output()
	kl_divergence = 0.5*tf.reduce_sum(1 + 2*z_logsigma - tf.sqr(z_mu) - tf.exp(2*z_logsigma), axis=1)

	x_mu = network['X'].get_output()

	if binary:
		x_mu = tf.clip_by_value(x_mu,1e-7,1-1e-7)
		log_likelihood = tf.reduce_sum(targets*tf.log(x_mu) + (1.0-targets)*tf.log(1.0-x_mu), axis=1)
	else:
		x_logsigma = tf.log(tf.sqrt(x_mu*(1-x_mu))) #layers.get_output(network['decode_logsigma'], deterministic=deterministic)
		log_likelihood = tf.reduce_sum(-0.5*tf.log(2*np.float32(np.pi))- x_logsigma - 0.5*tf.sqr(targets-x_mu)/T.exp(2*x_logsigma),axis=1)

	variational_lower_bound = -log_likelihood - kl_divergence
	predictions = x_mu

	return tf.reduce_mean(variational_lower_bound), predictions



def cost_function(predictions, targets, objective, **kwargs):

	if 'clip_value' in kwargs.keys():
		if kwargs['clip_value']:
			predictions = tf.clip_by_value(predictions,1e-7,1-1e-7)
		
	if objective == 'binary':   
		loss = -tf.reduce_mean(targets*tf.log(predictions) + (1-targets)*tf.log(1-predictions))

	elif objective == 'categorical':
		loss = -tf.reduce_mean(tf.reduce_sum(targets*tf.log(predictions), axis=1))
	
	elif objective == 'squared_error':    
		loss = tf.reduce_mean(tf.square(predictions - targets))
		
	return loss


def get_l1_parameters(net):    
	params = []
	for layer in net:
		if hasattr(net[layer], 'is_l1_regularize'):
			if net[layer].is_l1_regularize():
				variables = net[layer].get_variable()
				if isinstance(variables, list):
					for var in variables:
						params.append(var.get_variable())
				else:
					params.append(variables.get_variable())
	return merge_parameters(params)


def get_l2_parameters(net):    
	params = []
	for layer in net:
		if hasattr(net[layer], 'is_l2_regularize'):
			if net[layer].is_l2_regularize():
				variables = net[layer].get_variable()
				if isinstance(variables, list):
					for var in variables:
						params.append(var.get_variable())
				else:
					params.append(variables.get_variable())
	return merge_parameters(params)



def merge_parameters(params):
	all_params = []
	for param in params:
		all_params = tf.concat([all_params, tf.reshape(param, [-1,])], axis=0)
	return all_params
	