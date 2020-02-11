import numpy as np
import networkx as nx
from scipy.spatial.distance import cdist


def _cost_func(graph, node_u, node_v, player):
    """
    Simple piecewise definition of hex transition costs. Empty -> Allied, Allied -> Empty and Allied -> Allied have a
    small associated cost.
    :param graph: NetworkX Graph object to traverse.
    :param node_u:
    :param node_v:
    :param player: Which player stones are allied and which are opposing.
    :return:
    Scalar value.
    """
    weight_dict_p1 = {
        (-1, -1): 1,
        (-1, 1): 1,
        (-1, 2): 1e6,
        (1, -1): 1,
        (1, 1): 1,
        (1, 2): 1e6,
        (2, -1): 1e6,
        (2, 1): 1e6,
        (2, 2): 1e6,
    }
    weight_dict_p2 = {
        (-1, -1): 1,
        (-1, 1): 1e6,
        (-1, 2): 1,
        (1, -1): 1e6,
        (1, 1): 1e6,
        (1, 2): 1e6,
        (2, -1): 1,
        (2, 1): 1e6,
        (2, 2): 1,
    }
    u = graph.nodes[node_u]['owner']
    v = graph.nodes[node_v]['owner']
    if player == -1:
        return 1
    elif player == 1:
        return weight_dict_p1[(u, v)]
    else:
        return weight_dict_p2[(u, v)]


def _compute_hex_score(player, graph, valid_moves):
    """
    Evaluation function based on the hex state. Per hex a score is computed based on the adjacent spaces.
    :param player: Player considered as "self".
    :param graph: NetworkX Graph object.
    :param valid_moves: Deprecated. Used for testing.
    :return:
    Score for 'player' and opponent hexes.
    """

    # Graph ownership values are shift +1 in the Graph object. Player numbers are '0' or '1'.
    own_val = int(player) + 1
    opponent_val = int(not(player)) + 1
    # What values to assign to adjacent hexes. Negative weighting produces bad AI.
    value_dict = {
        -1: 3.5,
        own_val: 5.0,
        opponent_val: 0
    }

    occupied_self = [n for n in graph.nodes if graph.nodes[n]['owner'] is own_val]
    occupied_other = [n for n in graph.nodes if graph.nodes[n]['owner'] is opponent_val]
    self_score = 0
    for ocs in occupied_self:
        for neigh in graph.neighbors(tuple(ocs)):
            if not neigh == ocs:
                self_score += value_dict[graph.nodes[neigh]['owner']]

    other_score = 0
    for ocs in occupied_other:
        for neigh in graph.neighbors(tuple(ocs)):
            if not neigh == ocs:
                other_score += value_dict[graph.nodes[neigh]['owner']]
    return self_score, other_score


def _hex_heuristic(player, graph, valid_moves):
    """
    Hex evaluation function as a ratio of self_score and other_score.
    :param player: Player considered as "self".
    :param graph: NetworkX Graph object.
    :param valid_moves: Deprecated. Used for testing.
    :return:
    A numeric score for a given boardstate.
    """
    self_score, other_score = _compute_hex_score(player, graph, valid_moves)
    score = self_score #/ max((1, 2 * other_score))
    return np.max((0, score)), None


def _compute_distances(player, graph, valid_moves):
    """
    Evaluation function computed as the distances between hexes.
    :param player: Player considered as "self".
    :param graph: NetworkX Graph object.
    :param valid_moves: Deprecated. Used for testing.
    :return:
    List of distances to nodes belonging to each player.
    """
    own_val = int(player) + 1
    opponent_val = int(not(player)) + 1
    occupied_self = [n for n in graph.nodes if graph.nodes[n]['owner'] is own_val]
    occupied_other = [n for n in graph.nodes if graph.nodes[n]['owner'] is opponent_val]
    dist_to_self = []
    dist_to_other = []

    for o_self in occupied_self:
        aux = []
        for o_self2 in occupied_self:
             if o_self == o_self2:
                 pass
             else:
                aux.append(nx.shortest_path_length(graph, tuple(o_self2), o_self))
        dist_to_self.append(aux)

    for o_other in occupied_other:
        aux = []
        for o_other2 in occupied_other:
            if o_other == o_other2:
                pass
            else:
                aux.append(nx.shortest_path_length(graph, tuple(o_other2), o_other))
        dist_to_other.append(aux)
    return dist_to_self, dist_to_other


def _dist_self_min(player, graph,valid_moves):
    """
    Minimize distance to self.
    :param player: Player considered as "self".
    :param graph: NetworkX Graph object.
    :param valid_moves: Deprecated. Used for testing.
    :return:
    A numeric score for a given boardstate.
    """
    dist_to_self, _ = _compute_distances(player, graph, valid_moves)
    dist_to_self = dist_to_self[0]
    if len(dist_to_self) > 0:
        ind = np.argmin(dist_to_self)
        return dist_to_self[ind], valid_moves[ind]
    else:
        return 0, None


def _dist_other_max(player, graph, valid_moves):
    """
    Maximize distance to other.
    :param player: Player considered as "self".
    :param graph: NetworkX Graph object.
    :param valid_moves: Deprecated. Used for testing.
    :return:
    A numeric score for a given boardstate.
    """
    _, dist_to_other = _compute_distances(player, graph, valid_moves)

    if len(dist_to_other) > 0:
        ind = np.argmax(dist_to_other)
        return dist_to_other[ind], None
    else:
        return 0, None


def _dist_move_matrix(player, graph,valid_moves):
    """
    Evaluation function. Computes the distance matrix of all moves and select the smallest one.
    :param player:
    :param graph:
    :param valid_moves:
    :return:
    A numeric score for a given boardstate.
    """
    dist_to_self, dist_to_other = _compute_distances(player, graph, valid_moves)
    if len(dist_to_other) > 0 and len(dist_to_self) > 0 :
        aux = np.mean(cdist(np.expand_dims(dist_to_self, 1), np.expand_dims(dist_to_other, 1)), axis=0)
        ind = np.argmin(aux)
        return aux[ind], None
    else:
        return 0, None


def heuristic_eval(type):
    """
    Evaluation function lookup. Returns the type of heuristic used in evaluating the board state.
    :param type: String. Dictionary key.
    :return:
    Function handle
    """
    heuristic_dict = {
        'dist_self_min': _dist_self_min,
        'dist_other_max': _dist_other_max,
        'dist_move_matrix': _dist_move_matrix,
        'hex_heuristic': _hex_heuristic,
    }
    return heuristic_dict[type]
