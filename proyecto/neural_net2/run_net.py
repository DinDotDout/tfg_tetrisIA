from keras.models import load_model
from time import sleep
from neural_net.dqn_agent import DQNAgent
from datetime import datetime
from statistics import mean, median
import random
# from .logs import CustomTensorBoard
from tqdm import tqdm
import os
import copy
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


from neural_net import heuristic_calc as h_c
from tetris_game import tetris as tetris
from tetris_game.tetrisStructure import board as b

agent = None

# Run dqn with Tetris
def train():
    global agent

    env = b.Board()
    episodes = 10000
    max_steps = 800
    epsilon_stop_episode = 9500
    mem_size = 20000
    discount = 0.95
    batch_size = 512
    epochs = 1
    render_every = 50
    log_every = 50
    replay_start_size = 2000
    train_every = 20
    n_neurons = [32, 32]
    render_delay = None
    activations = ['relu', 'relu', 'linear']

    agent = DQNAgent(state_size = h_c.get_state_size(), loss = "huber_loss",
                     n_neurons=n_neurons, activations=activations,
                     epsilon_stop_episode=epsilon_stop_episode, mem_size=mem_size,
                     discount=discount, replay_start_size=replay_start_size)

    # log_dir = f'neural_net/logs/tetris-nn={str(n_neurons)}-mem={mem_size}-bs={batch_size}-e={epochs}-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    # log = CustomTensorBoard(log_dir=log_dir)

    scores = []

    for episode in tqdm(range(episodes)):
        env.reset()
        current_state = h_c.get_board_props(env)
        done = False
        steps = 0

        if episode % render_every == 0:
            render = True # init pygame window
            renderLast = False
            tetris.init()
        elif episode >= episodes-1:
            render = True
            renderLast = True # init pygame window
            tetris.init()
        else:
            render = False
            renderLast = False

        # Game
        while not done and (not max_steps or steps < max_steps):
            # piece = 0
            # if render:
            #     piece = copy.deepcopy(env.mainPiece)

            next_states = h_c.get_next_states(env)
            
            best_action, isExploration = agent.best_action(next_states)
            reward, done, _ = h_c.play(env, best_action[0], best_action[1], isExploration)
            if render:
                tetris.draw(env)
                if renderLast:
                    sleep(0.3)


            agent.add_to_memory(current_state, next_states[best_action], reward, done)
            current_state = next_states[best_action]
            steps += 1
            if steps == 500:
                print(steps)
        if render:
            tetris.end()
            
        scores.append(env.score)

        # Train
        if episode % train_every == 0:
            agent.train(batch_size=batch_size, epochs=epochs)

        # # Logs
        # if log_every and episode and episode % log_every == 0:
        #     avg_score = mean(scores[-log_every:])
        #     min_score = min(scores[-log_every:])
        #     max_score = max(scores[-log_every:])

        #     log.log(episode, avg_score=avg_score, min_score=min_score,
        #             max_score=max_score)
                    
        agent.save()
    # agent.save()

def test_model(agent):
    env = b.Board()    
    # current_state = h_c.get_board_props(env)
    done = False

    tetris.init()
    # Game
    while not done :
        
        next_states = h_c.get_next_states(env)
        best_action, isExploration = agent.best_action(next_states)
        reward, done, _ = h_c.play(env, best_action[0], best_action[1], isExploration)
        tetris.draw(env)
        # agent.add_to_memory(current_state, next_states[best_action], reward, done)

        # print(best_action, end = ": ")
        # print(next_states[best_action])
        # print()
        sleep(0.4)
        # input()
        # current_state =  next_states[best_action] # Estado en el que se supone nos deberemos encontrar tras realizar los moviemientos  
    tetris.end()

def test():
    load_net()
    test_model(agent)

def load_net():
    global agent
    if os.path.isfile('neural_net/models/tetris_model.h5'):
        model = load_model('neural_net/models/tetris_model.h5')
        agent = DQNAgent(model = model, state_size = h_c.get_state_size(), epsilon = 0)
    else:
        print("No neural net data stored")

def get_net_output(env):
    next_states = h_c.get_next_states(env) # analizar todos los siguientes estados posibles del tetris de la switch
    best_action = agent.best_action(next_states)

    piece = copy.deepcopy(env.mainPiece)

    _, _, piecePos = h_c.play(env, best_action[0], best_action[1]) # enviar secuencia de comandos a la swtich
    
    # tn.draw(env)
    # print("action: ", end = "")
    # print(best_action[0], end = ", ")
    # print(best_action[1])
    return best_action[0], best_action[1], piecePos, piece