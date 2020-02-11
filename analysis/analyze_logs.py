import os
import h5py
import numpy as np


def parse_logs(root_dir, game_to_check):
    idx_dict = {game: idx for idx, game in enumerate(game_to_check)}
    wins = np.zeros((len(game_to_check), len(game_to_check), 4))
    total_draws = []
    for game in game_to_check:
        draws = 0
        log_list = os.listdir(os.path.join(root_dir, game))
        idx1 = idx_dict[game]
        for log in log_list:
            if '.h5' in os.path.splitext(log):
                with h5py.File(os.path.join(root_dir, game, log), 'r') as h5_game_result:
                    game_result = h5_game_result[[*h5_game_result.keys()][0]]
                    player_won, colinear, surround = game_result['win'][()]
                    other_heuristic = game_result['p2']['heuristic'][()]
                    idx2 = idx_dict[other_heuristic]
                    time = game_result['time'][()]
                    if player_won == 1:
                        wins[idx1, idx2, 0] += 1
                        wins[idx1, idx2, 1] += colinear
                        wins[idx1, idx2, 2] += surround
                    elif player_won == 2:
                        wins[idx2, idx1, 0] += 0
                        wins[idx2, idx1, 1] += 0
                        wins[idx2, idx1, 2] += 0
                    else:
                        wins[idx1, idx2, 3] += 1
                        # wins[idx2, idx1, 3] += 1
                        draws += 1
        total_draws.append(draws)

    excluder = (np.ones(5) - np.eye(5))
    winrate = np.sum(wins[:, :, 0] * excluder, axis=1) / 20
    colinear_wins = np.sum(wins[:, :, 1] * excluder, axis=1) / 20
    surrounded_wins = np.sum(wins[:, :, 2] * excluder, axis=1) / 20
    for idx, game in enumerate(game_to_check):
        print('Winrate of {}: {:.2f} Colinear: {:.2f} Surround {:.2f}'.format(game, winrate[idx],
                                                                              colinear_wins[idx], surrounded_wins[idx]))



if __name__ == '__main__':
    log_path = 'D:\PycharmProjects\\andantino_logs'
    game_to_check = ['dist_self_min', 'dist_other_max',  'dist_other_self_min', 'dist_other_self_max', 'dist_move_matrix']
    parse_logs(log_path, game_to_check)