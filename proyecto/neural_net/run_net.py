from keras.models import load_model
from time import sleep
from neural_net.dqn_agent import DQNAgent
from datetime import datetime
from statistics import mean, median
import random
from .logs import CustomTensorBoard
from tqdm import tqdm
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from neural_net import heuristic_calc as h_c
from tetris_game import tetris as tn
from tetris_game.tetrisStructure import board as b


# Run dqn with Tetris
def dqn():
    env = b.Board()
    episodes = 2000
    max_steps = None
    epsilon_stop_episode = 1500
    mem_size = 20000
    discount = 0.95
    batch_size = 512
    epochs = 1
    render_every = 100
    log_every = 100
    replay_start_size = 2000
    train_every = 2000
    n_neurons = [32, 32]
    render_delay = None
    activations = ['relu', 'relu', 'linear']

    agent = DQNAgent(state_size = h_c.get_state_size(),
                     n_neurons=n_neurons, activations=activations,
                     epsilon_stop_episode=epsilon_stop_episode, mem_size=mem_size,
                     discount=discount, replay_start_size=replay_start_size)

    log_dir = f'neural_net/logs/tetris-nn={str(n_neurons)}-mem={mem_size}-bs={batch_size}-e={epochs}-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    log = CustomTensorBoard(log_dir=log_dir)

    scores = []

    for episode in tqdm(range(episodes)):
        env.reset()
        current_state = h_c.get_board_props(env, 0)
        done = False
        steps = 0

        if render_every and episode % render_every == 0:
            render = True # init pygame window
        else:
            render = False

        # Game
        while not done and (not max_steps or steps < max_steps):
            next_states, env = h_c.get_next_states(env)
            # print(next_states.values())
            best_state = agent.best_state(next_states.values())
            
            best_action = None
            for action, state in next_states.items():
                if state == best_state:
                    best_action = action
                    break

            reward, done = h_c.play(env, best_action[0], best_action[1], render=render,
                                    render_delay=render_delay)
            if render:
                tn.draw(env)
                # print()
                # sleep(0.8)

            agent.add_to_memory(current_state, next_states[best_action], reward, done)
            current_state = next_states[best_action]
            steps += 1
        if render:
            tn.end()
           
        scores.append(env.score)

        # Train
        if episode % train_every == 0:
            agent.train(batch_size=batch_size, epochs=epochs)

        # Logs
        if log_every and episode and episode % log_every == 0:
            avg_score = mean(scores[-log_every:])
            min_score = min(scores[-log_every:])
            max_score = max(scores[-log_every:])

            log.log(episode, avg_score=avg_score, min_score=min_score,
                    max_score=max_score)
                    
        agent.save()

def test_model(model):

    env = b.Board()
    agent = DQNAgent(model = model, state_size = h_c.get_state_size(), epsilon = 0)
    current_state = h_c.get_board_props(env, 0)
    done = False
    steps = 0
    max_steps = None
    
    render_delay = None
    render = True

    # Game
    while not done :
    # and (not max_steps or steps < max_steps):
        next_states, env = h_c.get_next_states(env) # analizar todos los siguientes estados posibles del tetris de la switch
        
        best_state = agent.best_state(next_states.values())
        
        best_action = None
        for action, state in next_states.items():
            if state == best_state:
                best_action = action
                break
        reward, done = h_c.play(env, best_action[0], best_action[1], render=render,
                                render_delay=render_delay) # enviar secuencia de comandos a la swtich
        # if reward > 11:
        

        # print(reward)
        tn.draw(env)
        # print(best_state)
        # sleep(2)
        sleep(0.8)
        # enviar secuencia de comandos a la switch
        current_state = next_states[best_action] # Estado en el que se supone nos deberemos encontrar tras realizar los moviemientos

def train():
    dqn()

def test():
    if os.path.isfile('neural_net/models/tetris_model.h5'):
        model = load_model('neural_net/models/tetris_model.h5')
        test_model(model)
    else:
        print("No neural net data stored")