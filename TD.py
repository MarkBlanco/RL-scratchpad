# HEADERS
import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
from easy21 import *

"""
This class implements the SARSA(lambda) reinforcement learning frea
"""
class TemporalDifference21:
    '''
    n_steps represents the number of steps ahead that TD learning will use to update state-action value estimations.
    If equal to '-1', TD-n is used with n equal to the trace length at the time of update. 
    Otherwise the learning range is exactly n_steps or trace length, whichever is shorter.
    '''
    def __init__(self, N0=100, n_steps=-1):
        # init an interal game instance:
        self._game = Easy21();

        # Set initial N for computation of epsilon parameter used with epsilon-greedy
        # policy (default policy). 
        self._N0 = float(N0)

        # Plus one oversizes state space to accomodate for single (-1, -1) terminal state.
        self._action_state_counts = np.zeros((11, 22, 2))
        self._action_state_values = np.zeros((11, 22, 2))

        if n_steps == 0:
            print("Warning: n_steps must be -1 or greater than 0." \
                "Defaulting to TD-n with n = trace length.")
        self._lookahead = n_steps

    # Run a TD episode and update Q(s,a) as simulation progresses.
    def run_episode(self):
        '''
        Run a game to completion. As the game runs, update the accumulated returns
        for each state, action pair based on the cumulative record of rewards and state trace.
        '''
        # List to keep track of states, actions, and rewards
        state_actions_rewards = []
        Q = self._action_state_values
        C = self._action_state_counts

        # Start the game:
        self._game.reset()
        # Get the current state:
        current_state = self._game.get_state()
        # Subtract one to use scores as indices.
        d_score, p_score = [x-1 for x in current_state]
        while not self._game._game_over:

            # Compute epsilon for this iteration:
            N0 = self._N0
            # Compute total number of visits to current state over all actions:
            N_st = float( np.sum(C[d_score, p_score, :]) )
            epsilon = N0/(N0 + N_st)

            # Apply epsilon randomness:
            r = random.random()
            if r < epsilon:
                best_action = random.randint(0,1)
            else:
                # Select the best action given what we know of the state-action estimates:
                best_action = np.argmax(Q[d_score, p_score, :])

            # Save old state:
            d_score_last = d_score
            p_score_last = p_score
            last_action = best_action

            # Take action
            reward, current_state, _ = self._game.player_plays( best_action )
            d_score, p_score = [ (x-1 if x != -1 else x) for x in current_state ]
            
            # Update state-action-reward trace:
            state_actions_rewards.append( (d_score_last, p_score_last, last_action, reward) )
            C[d_score_last, p_score_last, last_action] += 1
            # print(state_actions_rewards[-1])

            if self._game._game_over:
                state_actions_rewards.append( (-1, -1, 0, 0.0) )
                C[-1,-1,0] += 1

            # Update value estimates at the end of one action-taking iteration in the game:
            # (Do this for every state seen)
            for index, val in enumerate(state_actions_rewards):
                d_score_last, p_score_last, last_action, _ = val
                lookahead = min(self._lookahead, len(state_actions_rewards) - index - 1)
                if lookahead == -1:
                    # Lookahead -1 basically implements full-trace learning, but updated
                    # at each action-state change rather than at end of game.
                    l = len(state_actions_rewards) - index
                else:
                    l = lookahead+1
                for lookahead in range(l-1,l):
                    d_score_now, p_score_now, targ_act, _ = state_actions_rewards[index + lookahead] 
                    targ_val = Q[d_score_now, p_score_now, targ_act]
                    # Get rewards from the state at index up to but not including the target state:
                    rewards = [ x[3] for x in state_actions_rewards[index:index+lookahead] ]
                    # Compute the pre-target return (NOTE NO DISCOUNTING):
                    pretarget_return = np.sum(rewards)
                    # Update value of last state-action taken with last reward and estimated return 
                    # (value) of next action-state: 
                    old_value = Q[d_score_last, p_score_last, last_action]
                    count = C[d_score_last, p_score_last, last_action]
                    total_return = pretarget_return + targ_val
                    Q[d_score_last, p_score_last, last_action] = old_value + (total_return - old_value) / count