import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from tensorflow.keras import layers

from collections import deque
import numpy as np
import random
import copy

# Deep Q Learning Agent + Maximin
#
# This version only provides only value per input,
# that indicates the score expected in that state.
# This is because the algorithm will try to find the
# best final state for the combinations of possible states,
# in constrast to the traditional way of finding the best
# action for a particular state.
class DQNAgent:
    '''Deep Q Learning Agent + Maximin

    Args:
        state_size (int): Size of the input domain
        mem_size (int): Size of the replay buffer
        discount (float): How important is the future rewards compared to the immediate ones [0,1]
        epsilon (float): Exploration (probability of random values given) value at the start
        epsilon_min (float): At what epsilon value the agent stops decrementing it
        epsilon_stop_episode (int): At what episode the agent stops decreasing the exploration variable
        n_neurons (list(int)): List with the number of neurons in each inner layer
        activations (list): List with the activations used in each inner layer, as well as the output
        loss (obj): Loss function
        optimizer (obj): Otimizer used
        replay_start_size: Minimum size needed to train
    '''
 
    def __init__(self, state_size, model = None, mem_size=10000, discount=0.95,
                 epsilon=1, epsilon_min=0, epsilon_stop_episode=500,
                 n_neurons=[32,32], activations=['relu', 'relu', 'linear'],
                 loss='mse', optimizer='adam', replay_start_size=None, metrics = "mean_squared_error"):

 
        assert len(activations) == len(n_neurons) + 1

        self.state_size = state_size
        self.memory = deque(maxlen=mem_size)
        self.discount = discount
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = (self.epsilon - self.epsilon_min) / (epsilon_stop_episode)
        self.n_neurons = n_neurons
        self.activations = activations
        self.loss = loss
        self.optimizer = optimizer
        self.metrics = metrics
        if not replay_start_size:
            replay_start_size = mem_size / 2
        self.replay_start_size = replay_start_size
        if model:
            self.model = model
            return
        self.model = self._build_model()


    def _build_model(self):
        '''Builds a Keras deep neural network model'''
        model = Sequential()
        model.add(Dense(self.n_neurons[0], input_dim=self.state_size, activation=self.activations[0]))

        for i in range(1, len(self.n_neurons)):
            model.add(Dense(self.n_neurons[i], activation=self.activations[i]))

        model.add(Dense(1, activation=self.activations[-1]))

        model.compile(loss=self.loss, optimizer=self.optimizer, metrics=self.metrics)
        
        return model

    def _build_model2(self):
        shape_main_grid = (1, 20, 10, 1)
        shape_hold_next = (1, 1 * 2 + 1 + 6 * 7)
        
        '''Builds a Keras deep neural network model'''
        main_grid_input = keras.Input(shape=shape_main_grid[1:], name="main_grid_input")
        a = layers.Conv2D(
            64, 6, activation="relu", input_shape=shape_main_grid[1:]
        )(main_grid_input)
        a1 = layers.MaxPool2D(pool_size=(15, 5), strides=(1, 1))(a)
        a1 = layers.Flatten()(a1)
        a2 = layers.AvgPool2D(pool_size=(15, 5))(a)
        a2 = layers.Flatten()(a2)

        b = layers.Conv2D(
            256, 4, activation="relu", input_shape=shape_main_grid[1:]
        )(main_grid_input)
        b1 = layers.MaxPool2D(pool_size=(17, 7), strides=(1, 1))(b)
        b1 = layers.Flatten()(b1)
        b2 = layers.AvgPool2D(pool_size=(17, 7))(b)
        b2 = layers.Flatten()(b2)

        hold_next_input = keras.Input(shape=shape_hold_next[1:], name="hold_next_input")

        x = layers.concatenate([a1, a2, b1, b2, hold_next_input])
        x = layers.Dense(128, activation="relu")(x)
        x = layers.Dense(64, activation="relu")(x)
        critic_output = layers.Dense(1)(x)  # activation=None -> 'linear'

        model_new = keras.Model(
            inputs=[main_grid_input, hold_next_input],
            outputs=critic_output
        )

        model_new.summary()

        return model_new

    def add_to_memory(self, current_state, next_state, reward, done):
        '''Adds a play to the replay memory buffer'''
        self.memory.append((current_state, next_state, reward, done))


    def random_value(self):
        '''Random score for a certain action'''
        return random.random()


    def predict_value(self, state):
        '''Predicts the score for a certain state'''
        return self.model.predict(state)[0]


    def act(self, state):
        '''Returns the expected score of a certain state'''
        state = np.reshape(state, [1, self.state_size])
        if random.random() < self.epsilon:
            return self.random_value()
        else:
            return self.predict_value(state)


    def best_action(self, states):
        '''Returns the best action for a given collection of states'''
        max_value = None
        best_action = None
        if random.random() < self.epsilon:
            return random.choice(list(states.keys())), True
        else:

            #CHANGE TO ARGMAX???
            # print(list(states))
            for action, state in states.items():
                # print("state: ", end ="")
                # print(state.value)
                value = self.predict_value(np.reshape(state, [1, self.state_size]))
                if not max_value or value > max_value:
                    max_value = value
                    best_action = action
                    best_state = state
     
            return best_action, False

    def save(self):
        self.model.save('neural_net/models/tetris_model.h5')

    def train(self, batch_size=32, epochs=3):
        '''Trains the agent'''
        n = len(self.memory)
        if n >= self.replay_start_size and n >= batch_size:

            batch = random.sample(self.memory, batch_size)
            
            # Get the expected score for the next states, in batch (better performance)
            next_states = np.array([x[1] for x in batch])
            next_qs = [x[0] for x in self.model.predict(next_states)]

            x = []
            y = []

            # Build xy structure to fit the model in batch (better performance)
            for i, (state, _, reward, done) in enumerate(batch):
                if not done:
                    # Partial Q formula
                    new_q = reward + self.discount * next_qs[i]
                else:
                    new_q = reward
                x.append(state)
                y.append(new_q)

            # Fit the model to the given values
            self.model.fit(np.array(x), np.array(y), batch_size=batch_size, epochs=epochs, verbose=0)

            # Update the exploration variable
            if self.epsilon > self.epsilon_min:
                self.epsilon -= self.epsilon_decay