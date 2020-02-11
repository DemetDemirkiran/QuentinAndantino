from itertools import repeat
import networkx as nx
import numpy as np
import copy
from engine. mp_engine import check_surrounded_mp
from collections import Counter
from multiprocessing.pool import Pool
from multiprocessing import Process
from engine.heuristic import heuristic_eval
from time import time
from engine.zobrist import ZobristHash

# Hardcoded Reward value and max time per iterative deepening level.
_REWARD = 1e7
_MAX_TIME = 10 * 60 # 10 minutes max * 60 s / m
_MAX_MOVES = 25 # In Andantino up to 25 stones may be played
_TIME_MOVE = _MAX_TIME / _MAX_MOVES



class GameEngine:
    def __init__(self, board, first_player):

        def _visible(cell):
            """
            Checks if hexes are visible to avoid having an invalid representation of the board. Visibility is determined
            by hex's alpha channel value (transparency).
            :param cell: Tuple (x,y).
            :return:
            True if visible false otherwise.
            """
            if board.map.fog[cell][3] == 0:
                return True
            return False

        self.first_type = first_player.type

        visible_cells = [cell for cell in board.map.fog if _visible(cell)]

        self.graph = nx.Graph()
        self.graph.add_nodes_from(visible_cells)
        for node in self.graph.nodes:
            self.graph.nodes[node]['owner'] = -1
            neigh = [cell for cell in board.map.spread(node, radius=1) if _visible(cell)]
            self.graph.add_edges_from(zip(repeat(node, len(neigh)), neigh))
        nx.set_edge_attributes(self.graph, {e: 1 for e in self.graph.edges()}, 'cost')
        aux = np.array([np.array(n) for n in self.graph.nodes])
        self.min_x = np.min(aux[:, 0])
        self.max_x = np.max(aux[:, 0])
        self.min_y = np.min(aux[:, 1])
        self.max_y = np.max(aux[:, 1])
        self.process_pool = Pool(4)

        # Transposition table
        self.zhash = ZobristHash(self.graph)
        self.transposition_table = dict()
        self.max_depth = 2

    def to_dict(self):
        """
        When called returns a dictionary with all the information required to load the game state. Objects can't be
        pickled and are automatically instanced so they are not saved.
        :return:
        Dictionary containing class relevant data.
        """
        engine_dict = dict()
        engine_dict['graph'] = self.graph
        engine_dict['min_x'] = self.min_x
        engine_dict['max_x'] = self.max_x
        engine_dict['min_y'] = self.min_y
        engine_dict['max_y'] = self.max_y
        return engine_dict

    def from_dict(self, engine_dict):
        """
        Set the object's attributes according to a pre-loaded dictionary.
        :param engine_dict: Dictionary containing engine attributes.
        :return:
        """
        self.min_x = engine_dict['min_x']
        self.max_x = engine_dict['max_x']
        self.min_y = engine_dict['min_y']
        self.max_y = engine_dict['max_y']

    def _cost_func(self, node_u, node_v, player):
        """
        Simple piecewise definition of hex transition costs. Empty -> Allied, Allied -> Empty and Allied -> Allied have a
        small associated cost.
        :param node_u:
        :param node_v:
        :param player: Which player stones are allied and which are opposing.
        :return:
        Scalar value.
        """
        weight_dict_p1 = {
            (-1, -1): 1,
            (-1, 1): 1e5,
            (-1, 2): 1e6,
            (1, -1): 1e5,
            (1, 1): 1,
            (1, 2): 1e6,
            (2, -1): 1e6,
            (2, 1): 1e6,
            (2, 2): 1e6,
        }
        weight_dict_p2 = {
            (-1, -1): 1,
            (-1, 1): 1e6,
            (-1, 2): 1e5,
            (1, -1): 1e6,
            (1, 1): 1e6,
            (1, 2): 1e6,
            (2, -1): 1e5,
            (2, 1): 1e6,
            (2, 2): 1,
        }
        u = self.graph.nodes[node_u]['owner']
        v = self.graph.nodes[node_v]['owner']
        if player == -1:
            return 1
        elif player == 1:
            return weight_dict_p1[(u, v)]
        else:
            return weight_dict_p2[(u, v)]

    def _minimax(self, cur_depth, hex_dict, is_max_turn, heuristic_func, timer, player, alpha=float('-inf'), beta=float('inf')):
        """
        Performs minimax tree search.
        :param cur_depth: Current search depth.
        :param hex_dict: Dictionary containing two sets of occupied hexes. One per player.
        :param is_max_turn: If it is the maximizer's turn.
        :param heuristic_func: What evaluation function to use.
        :param timer: Sets a time limit for the search.
        :param player: Player identifier. Either 0 or 1.
        :param alpha: Parameter alpha-beta pruning.
        :param beta: Parameter alpha-beta pruning.
        :return:
        Returns the value of the best move found and the move coordinates (x,y)
        """
        best_value = float('-inf') if is_max_turn else float('inf')
        best_move = None
        valid_moves = self.check_valid_moves()
        # Shuffle if not empty
        try:
            valid_moves = valid_moves[np.random.choice(range(len(valid_moves)), len(valid_moves), replace=False)]
        except TypeError:
            pass

        # Compare elapsed time vs max allowed time.
        time_delta = time() - timer[0]
        # If search limiters are met evaluate node.
        if cur_depth <= 0 or time_delta >= timer[1]:
            # Check for existence in the transposition table, otherwise compute.
            hashkey = self.zhash.hash(self.graph)
            try:
                result, _, _ = self.transposition_table[hashkey]
            except KeyError:
                game_result = self.check_for_game_end(hex_dict[0], hex_dict[1])
                hf = heuristic_func(player, self.graph, valid_moves)

                if 1:
                    if game_result[int(not player)]:
                        result = _REWARD
                        print(1, player, is_max_turn, result)
                    elif game_result[int(player)]:
                        result = -_REWARD
                        print(2, player, is_max_turn, result)
                    else:
                        result = hf[0]

                self.transposition_table[hashkey] = (result, None, cur_depth)
            return result, None
        # If search limiters are not met search the tree alternating between max and min.
        else:
            for vm in valid_moves:
                vm = tuple(vm)
                # Simulate play. Done only on the board representation graph.
                self._set_temporary_owner(vm, is_max_turn + 1)
                hex_dict[is_max_turn].add(vm)

                eval_child, move_child = self._minimax(cur_depth - 1, hex_dict, not is_max_turn, heuristic_func, timer, not player, alpha, beta)
                # Undo play. Done only on the board representation graph.
                self._set_temporary_owner(vm, -1)
                hex_dict[is_max_turn].remove(vm)

                # Alpha beta pruning
                if is_max_turn and best_value < eval_child:
                    best_value = eval_child
                    best_move = vm
                    alpha = max(alpha, best_value)
                    if beta <= alpha:
                        break

                elif (not is_max_turn) and best_value > eval_child:
                    best_value = eval_child
                    best_move = vm
                    beta = min(beta, best_value)
                    if beta <= alpha:
                        break

                time_delta = time() - timer[0]
                if time_delta >= timer[1]:
                    break

            return best_value, best_move

    def check_valid_moves(self):
        """
        Check which hexes are valid. Different logic when going first as first move has slightly different rules.
        :return:
        List of valid moves.
        """
        # Serves as move tree to search
        occupied = [n for n in self.graph.nodes if self.graph.nodes[n]['owner'] is not -1]
        if len(occupied) == 0:
            # Fixed start for this board size
            valid_moves = list(self.graph.neighbors((16, 9)))
            valid_moves.append((16, 9))
        elif len(occupied) == 1:
            # Fixed start for this board size
            if occupied[0] == (16, 9):
                neigh = [m for n in occupied for m in list(self.graph.neighbors(n))]
                neigh_counts = Counter(neigh)
                # Remove already played hexes
                for occ in occupied:
                    neigh_counts[occ] = 0
                valid_moves = np.array(list(neigh_counts.keys()))[np.array(list(neigh_counts.values())) > 0]
            else:
                valid_moves = [(16, 9)]
        else:
            neigh = [m for n in occupied for m in list(self.graph.neighbors(n))]
            neigh_counts = Counter(neigh)
            # Remove already played hexes
            for occ in occupied:
                neigh_counts[occ] = 0
            valid_moves = np.array(list(neigh_counts.keys()))[np.array(list(neigh_counts.values())) > 1]
            if len(valid_moves) == 0:
                valid_moves = np.array(list(neigh_counts.keys()))[np.array(list(neigh_counts.values())) > 0]
        return valid_moves

    def _set_temporary_owner(self, node, player):
        """
        Helper function to simulate plays. Changes are only done on the representation graph.
        :param node: Tuple (x,y).
        :param player: Player identifier.
        :return:
        """
        self.graph.nodes[node]['owner'] = int(player)
        neighbors = list(self.graph.neighbors(node))
        nx.set_edge_attributes(
            self.graph,
            {(node, neigh): self._cost_func(node, neigh, player) for neigh in neighbors},
            name='cost'
        )

    def set_owner(self, node, player):
        """
        MAkes changes to the graph. Changes are initiated from the GameInstace object.
        :param node: Tuple (x,y).
        :param player: Player identifier.
        :return:
        """
        # Separate board according to played pieces
        player = int(player)
        if player == -1:
            self.graph.nodes[node]['owner'] = player
            neighbors = list(self.graph.neighbors(node))
            nx.set_edge_attributes(
                self.graph,
                {(node, neigh): self._cost_func(node, neigh, player) for neigh in neighbors},
                name='cost')

        elif self.graph.nodes[node]['owner'] == -1:
            self.graph.nodes[node]['owner'] = player
            neighbors = list(self.graph.neighbors(node))
            nx.set_edge_attributes(
                self.graph,
                {(node, neigh): self._cost_func(node, neigh, player) for neigh in neighbors},
                name='cost')
        else:
            raise AttributeError('Cell already owned.')

    def _check_colinear(self, hexes, player, line_length=4, details=False):
        """
        Colinearity check. Per occupied hex check lines of 5 spaces in the three possible directions.
        :param hexes: Tuple (x,y).
        :param player: Player identifier.
        :return:
        Returns True if an uninterrupted line of 5 stones is found.
        """

        def _make_lines2(x, y, x_min, x_max, y_min, y_max, length_win):
            """
            Generator for lines of length = length_win in 3 directions.
            :param x: Hex x.
            :param y: Hex y.
            :param x_min: Smallest x value for the line.
            :param x_max: Largest x value for the line.
            :param y_min: Smallest y value for the line.
            :param y_max: Largest y value for the line.
            :param length_win: Length of the line necessary for a win
            :return:
            List of lists for the coordinates of the lines.
            """
            lines = [
                list(zip(range(x_min, x_max), repeat(y, length_win))),
                list(zip(range(x_min, x_max), range(y_min, y_max))),
                list(zip(repeat(x, length_win), range(y_min, y_max)))
            ]
            return lines

        # Hardcoded as per the game rules.
        length_win = 5
        for h in hexes:
            x, y = h
            # Move two spaces back on x and y.
            x_min = int(x - (length_win - 1) / 2)
            y_min = int(y - (length_win - 1) / 2)
            # Move two spaces forward on x and y.
            # Added one for non-inclusive end.
            x_max = int(x + (length_win - 1) / 2) + 1
            y_max = int(y + (length_win - 1) / 2) + 1
            # Per hex check the lines to check.
            lines = _make_lines2(x, y, x_min, x_max, y_min, y_max, length_win)
            aux = []
            aux_line = []
            # Check how many of the hexes have to stones belonging to player.
            for line in lines:
                try:
                    ownership = [self.graph.nodes[tuple(n)]['owner'] for n in line]
                    l = [en for en, o in enumerate(ownership) if o == player]
                    aux.append(sum(np.diff(sorted(l)) == 1))
                    aux_line.append(line)
                except KeyError:
                    aux.append(0)
            if np.max(aux) >= line_length:
                if not details:
                    return 1
                else:
                    return 1, aux_line[np.argmax(aux)]
        if not details:
            return 0
        else:
            return 0, aux_line[np.argmax(aux)]

    def check_for_game_end(self, player1_hex, player2_hex, details=False):
        """
        Check whether one (or more) of the game conditions have been met.
        :param player1_hex: Set of hexes owned by player 1.
        :param player2_hex: Set of hexes owned by player 2.
        :param details: Return specific game end results. Used for logging.
        :return:
        Boolean of game end conditions.
        """
        player1_hex = np.array(list(player1_hex))
        player2_hex = np.array(list(player2_hex))

        surrounded1 = check_surrounded_mp(self.graph, player2_hex, self.process_pool)
        surrounded2 = check_surrounded_mp(self.graph, player1_hex, self.process_pool)

        colinear1 = self._check_colinear(player1_hex, 1)
        colinear2 = self._check_colinear(player2_hex, 2)
        if details:
            return surrounded1, colinear1, surrounded2, colinear2
        else:
            return surrounded1 or colinear1, surrounded2 or colinear2

    def ai_move(self, player1_hex, player2_hex, heuristic):
        """
        Select a hex to play for the AI.
        :param player1_hex: Set of hexes owned by player 1.
        :param player2_hex: Set of hexes owned by player 2.
        :param player: Player indicator.
        :param heuristic: Which evaluation function to use.
        :return:
        Tuple (x,y) of best move to make.
        """
        heuristic_func = heuristic_eval(heuristic)
        hex_dict = dict()
        if self.first_type == 'ai':
            hex_dict[0] = copy.deepcopy(player1_hex)
            hex_dict[1] = copy.deepcopy(player2_hex)
            is_max = True
            player = 0
            max_depth = 8
        else:
            hex_dict[0] = copy.deepcopy(player1_hex)
            hex_dict[1] = copy.deepcopy(player2_hex)
            is_max = 1
            player = 0
            max_depth = 3



        time_to_move = _TIME_MOVE * 0.75

        start_time = time()
        iterative_deep_step = 1
        val = 0
        move = None
        while time() - start_time < time_to_move:
            val_aux, move_aux = self._minimax(iterative_deep_step, hex_dict, is_max, heuristic_func, (start_time, time_to_move), player)
            iterative_deep_step += 1
            if val_aux > val:
                move = move_aux
                val = val_aux

            if iterative_deep_step >= max_depth:
                break

        return tuple(move)