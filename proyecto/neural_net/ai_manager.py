import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '4'
import numpy as np
import random
import pickle
import time
import multiprocessing
import psutil
import copy
import sys

# Deep learning libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# My libraries
from neural_net import heuristic_calc as h_c
from tetris_game import tetris as tetris

from tetris_game.tetrisStructure import board as b
import tetris_game.tetrisStructure.piece as piece

np.set_printoptions(threshold=sys.maxsize)


OUTER_MAX = 20
CPU_MAX = 99

FOLDER_NAME = 'neural_net/IAs/tetris_regular7bagChosen/'

OUT_START = 20


# size dependent
nPieces = 7
shape_main_grid = (1, b.Board.killHeight-1, b.Board.gridSizeX, 1)
shape_hold_next = (1, 1 * 2 + 1 + 6 * nPieces)


gamma = 0.95
epsilon = 0.06

current_avg_score = 0
rand = random.Random()
penalty = -500

# cpu_count = min(psutil.cpu_count(logical=False), CPU_MAX)

model = None
# model = keras.models.load_model("neural_net/"+FOLDER_NAME + 'whole_model/outer_{}'.format(OUT_START))

def make_model_conv2d():
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

    model = keras.Model(
        inputs=[main_grid_input, hold_next_input],
        outputs=critic_output
    )

    model.summary()
    model.compile(
        optimizer=keras.optimizers.Adam(0.001),
        loss='huber_loss',
        metrics='mean_squared_error'
    )
    model.save(FOLDER_NAME + 'whole_model/outer_{}'.format(0))
    print('model initial state has been saved')
    return model

# Returns
def best_move(model, states, moves, rewards, epsilon = 0):
    '''Returns the best action for a given collection of states'''
    # Let the net chose or explore
    rand_fl = random.random()
    if rand_fl > epsilon:
        q = rewards + model(states)

        # for j in range(len(states)):
        #     if states.gameOver[j]:
        #         q[j] = rewards[j]
        best = tf.argmax(q).numpy()[0]
        chosen = best
    else:       
        # uniform probability
        chosen = random.randint(0, len(states) - 1)
    
    return chosen

def testing(max_games=1, mode='piece', is_gui_on=True):
    global model
    max_steps_per_episode = None
    seed = None

    env = b.Board()

    episode_count = 0
    total_score = 0

    pause_time = 1.0
    tetris.init()
    totalSteps = 0
    while True and episode_count < max_games:
        steps = 0
        done = False
        env.reset()
        while not done and (not max_steps_per_episode or steps < max_steps_per_episode):
            possible_states, scores, dones, _, _, moves, env = h_c.get_next_states(env)

            # Get reward according to move
            rewards = h_c.get_reward(scores, dones)

            # Choose best actions
            chosen = best_move(model, possible_states, moves, rewards)
            best_moves = moves[chosen]

            # Perform selected move
            h_c.play(env, best_moves[0], best_moves[1])
            endEvent = tetris.draw(env)
            steps += 1
            done = env.gameOver

            if endEvent: # If window is closed exit testing
                return

        totalSteps += steps
        episode_count += 1
        total_score += env.current_state.score
        print('episode #{}:   score:{}   plays:{}'.format(episode_count, env.current_state.score, steps))
        
    tetris.end()

    print('average score = {:7.2f}'.format(total_score / max_games))


def get_data_from_playing_cnn2d(model_filename, target_size=8000, max_steps_per_episode=2000, proc_num=0,
                                queue=None):
    tf.autograph.set_verbosity(3) # Do not print info to cmd if training
    model = keras.models.load_model(model_filename)
    if model is None:
        print('ERROR: model has not been loaded.')
        exit()

    global epsilon
    if proc_num == 0:
        epsilon = 0

    data = list()
    env = b.Board()
    episode_max = 1000
    total_score = 0
    avg_score = 0
    for episode in range(episode_max):
        steps = 0
        done = False
        env.reset()
        episode_data = list()
        while not done and (not max_steps_per_episode or steps < max_steps_per_episode):
                possible_states, scores, dones, _, _, moves, env = h_c.get_next_states(env)
        for step in range(max_steps_per_episode):
            # current gamestate metrics and next pieces
            current_state = h_c.get_board_props(env) # get it out of the loop so that we don't have to compute it each time?

            # possible_states contains grid metrics and pieces
            possible_states, scores, dones, is_include_hold, is_new_hold, moves, env = h_c.get_next_states(env) 

            rewards = h_c.get_reward(scores, dones)
            chosen = best_move(model, possible_states, moves, rewards)

            pool_size = 7 # n pieces

            # if hold was empty, then we don't know what's next; if hold was not empty, then we know what's next!
            if is_include_hold and not is_new_hold:
                possible_states[1][:-1, -pool_size:] = 0
                
            else:
                possible_states[1][:, -pool_size:] = 0

            best_moves = moves[chosen]

            # Perform according moves to leave env as expected
            h_c.play(env, best_moves[0], best_moves[1])

            # current gamestate, next chosen gamestate, scores, done
            episode_data.append(
                (current_state, (possible_states[0][chosen], possible_states[1][chosen]), scores[chosen], dones[chosen]))

            done = env.gameOver

        data += episode_data
        total_score += env.score
        if len(data) > target_size:
            print('proc_num: #{:<2d} | total episodes:{:<4d} | avg score:{:<7.2f} | data size:{}'.format(
                proc_num, episode + 1, total_score / (episode + 1), len(data)))
            avg_score = total_score / (episode + 1)
            break

    if queue is not None:
        queue.put((data, avg_score), block=False)
        return

    return data, avg_score


def training(outer_start=0, outer_max=100):
    global model
    # outer_max: update samples
    inner_max = 5  # update target
    epoch_training = 5  # model fitting times
    batch_training = 512

    buffer_new_size = 20000
    buffer_outer_max = 1
    history = None
    # print('Found {} physical CPUs'.format(cpu_count))

    for outer in range(outer_start + 1, outer_start + 1 + outer_max):
        print('======== outer = {} ========'.format(outer))
        time_outer_begin = time.time()

        # 1. collecting data.
        buffer = list()

        # getting new samples
        new_buffer = collect_samples_multiprocess_queue(model_filename=FOLDER_NAME + f'whole_model/outer_{outer - 1}',
                                                        outer=outer - 1, target_size=buffer_new_size)
        save_buffer_to_file(FOLDER_NAME + f'dataset/buffer_{outer}.pkl', new_buffer)
        buffer += new_buffer

        # Load more samples
        for i in range(max(1, outer - buffer_outer_max + 1), outer):
            buffer += load_buffer_from_file(filename=FOLDER_NAME + 'dataset/buffer_{}.pkl'.format(i))

        # Randomize information order to get random batche
        random.shuffle(buffer)

        # 2. calculating target
        # s1 and s2 (prev state)
        # s1_ and s2_ (next state)
        # r_ reward
        # env done
        s1, s2, s1_, s2_, r_, dones_ = process_buffer_best(buffer)

        buffer_size = len(buffer)
        new_buffer_size = len(new_buffer)
        del buffer
        del new_buffer

        for inner in range(inner_max):
            print(f"      ======== inner = {inner + 1}/{inner_max} =========")
            target = list()

            # Loop trhough all batches (mini batch without replacement)
            for i in range(int(s1.shape[0] / batch_training) + 1):

                # Select batch beginning
                start = i * batch_training

                # Select batch end
                end = min((i + 1) * batch_training, s1.shape[0] + 1)

                # Add all predictions to memory
                target.append(
                    model((s1_[start:end, :, :, :], s2_[start:end, :]), training=False).numpy().reshape(-1) + r_[start:end])

            # Format memory
            target = np.concatenate(target)

            # When it's gameover, Q[s'] must not be added
            for i in range(len(dones_)):
                if dones_[i]:
                    target[i] = r_[i]

            # Apply gamma to predictions
            target = target * gamma

            # Fit the model to the given values
            history = model.fit((s1, s2), target, batch_size=batch_training, epochs=epoch_training, verbose=1)

            print('      loss = {:8.3f}   mse = {:8.3f}'.format(history.history['loss'][-1],
                                                                history.history['mean_squared_error'][-1]))

        model.save(FOLDER_NAME + 'whole_model/outer_{}'.format(outer))
        model.save_weights(FOLDER_NAME + 'checkpoints_dqn/outer_{}'.format(outer))

        time_outer_end = time.time()
        text_ = 'outer = {:>4d} | pre-training avg score = {:>8.3f} | loss = {:>8.3f} | mse = {:>8.3f} |' \
                ' dataset size = {:>7d} | new dataset size = {:>7d} | time elapsed: {:>6.1f} sec | penalty = {:>7d} | gamma = {:>6.3f}\n' \
            .format(outer, current_avg_score, history.history['loss'][-1], history.history['mean_squared_error'][-1],
                    buffer_size, new_buffer_size, time_outer_end - time_outer_begin, penalty, gamma
                    )
        append_record(text_)
        print('   ' + text_)


def save_buffer_to_file(filename, buffer):
    from pathlib import Path
    Path(FOLDER_NAME + 'dataset').mkdir(parents=True, exist_ok=True)
    with open(filename, 'wb') as f:
        pickle.dump(buffer, f)


def load_buffer_from_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def process_buffer_best(buffer):
    s1 = list()
    s2 = list()
    s1_ = list()
    s2_ = list()
    add_scores = list()
    dones_ = list()
    for row in buffer:
        s1.append(row[0][0])
        s2.append(row[0][1])
        s1_.append(row[1][0])
        s2_.append(row[1][1])
        add_scores.append(row[2])
        dones_ += [row[3]]

    s1 = np.concatenate(s1)
    s2 = np.concatenate(s2)
    s1_ = np.concatenate(s1_).reshape(s1.shape)
    s2_ = np.concatenate(s2_).reshape(s2.shape)
    r_ = h_c.get_reward(add_scores, dones_)
    r_ = np.concatenate(r_)
    return s1, s2, s1_, s2_, r_, dones_

def append_record(text, filename=None):
    if filename is None:
        filename = FOLDER_NAME + 'record.txt'
    with open(filename, 'a') as f:
        f.write(text)


def collect_samples_multiprocess_queue(model_filename, outer=0, target_size=10000):
    # global cpu_count
    timeout = 800
    
    cpu_count = min(multiprocessing.cpu_count(), CPU_MAX)
    jobs = list()
    q = multiprocessing.Queue()
    for i in range(cpu_count):
        p = multiprocessing.Process(target=get_data_from_playing_cnn2d,
                                    args=(
                                        model_filename, int(target_size / cpu_count), 1000, i, q))
        jobs.append(p)
        p.start()

    data = list()
    scores = list()

    for i in range(cpu_count):
        d_, s_ = q.get(timeout=timeout)
        data += d_
        scores.append(s_)

    i = 0
    for proc in jobs:
        proc.join()
        i += 1

    # average score is max(scores) because it's the process with eps = 0
    print(f'end multiprocess: total data length: {len(data)} | avg score: {max(scores)}')
    global current_avg_score
    current_avg_score = max(scores)

    return data


def load_model(filepath = FOLDER_NAME + 'whole_model/outer_{}'.format(OUT_START)):
    '''Loads a model given a file path'''
    global model
    if os.path.isdir(filepath):
        model = keras.models.load_model(filepath)
        return True
    else:
        print("Model not found")
        return False

        

def test():
    found = load_model(FOLDER_NAME + 'whole_model/outer_{}'.format(OUT_START))
    if not found:
        return
    testing(mode='step', is_gui_on=True)

def train():
    if OUT_START == 0:
        make_model_conv2d()
    found = load_model(FOLDER_NAME + 'whole_model/outer_{}'.format(OUT_START))
    if not found:
        return
    training(outer_start=OUT_START, outer_max=OUTER_MAX)


def get_net_output(env):
    '''Get net output given an environment with a certain state'''
    global model
    possible_states, scores, dones, _, _, moves, env = h_c.get_next_states(env)

    # Get reward according to move
    rewards = h_c.get_reward(scores, dones)

    # Choose best actions
    chosen = best_move(model, possible_states, moves, rewards)
    best_action = moves[chosen]

    piecePos, rotatedPiece, lines = h_c.play(env, best_action[0], best_action[1]) 
    
    return best_action[0], best_action[1], piecePos, rotatedPiece, lines, env