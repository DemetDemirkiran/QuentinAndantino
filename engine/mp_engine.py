import networkx as nx
import numpy as np
from scipy.spatial.distance import pdist, squareform

from functools import partial


def _l2_dist(u, v):
    """
    L2 distance function. To be used in the A* algorithm as heuristic function.
    :param u: Tuple (x1, y1)
    :param v: Tuple (x2, y2)
    :return:
    L2 distance of two points in space.
    """
    return np.linalg.norm(np.array(u) - np.array(v))


def _manhattan_dist(u, v):
    """
    L1 distance function. To be used in the A* algorithm as heuristic function.
    :param u: Tuple (x1, y1)
    :param v: Tuple (x2, y2)
    :return:
    L1 distance of two points in space.
    """
    D = 1
    x1, y1 = u
    x2, y2 = v
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    return D * (dx + dy)


def _cheby_dist(u, v):
    """
    Modified L1 distance function. To be used in the A* algorithm as heuristic function.
    :param u: Tuple (x1, y1)
    :param v: Tuple (x2, y2)
    :return:
    Chebyshev distance of two points in space.
    """
    D = 1
    D2 = 1
    x1, y1 = u
    x2, y2 = v
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    return (dx + dy) + (D2 - 2 * D) * min(dx, dy)


def _surrounded_logic(graph, nodes, weight='cost'):
    """
    Underlying logic for multiprocessed shortest-path finding. This function is executed for each pair of nodes.
    :param graph: NetworkX Graph to traverse.
    :param nodes: Tuple of nodes as Source and Target.
    :param weight: Weighting that determines the cost of moving from one hex to another.
    :return:
    Length of the shortest path.
    """
    source, target = nodes
    dist = nx.astar_path_length(graph,
                                tuple(source),
                                tuple(target),
                                heuristic=_manhattan_dist,
                                weight=weight)

    return dist


def check_surrounded_mp(graph, hexes, process_pool):
    """
    Multi-processed "check_surrounded" function.
    :param graph: NetworkX Graph to traverse.
    :param hexes: Hexes occupied by a player.
    :param process_pool: Multiprocess object.
    :return:
    Returns true if at least a piece is surrounded. False otherwise.
    """

    # Create a partial function to avoid having to copy references to the graph objects repeatedly.
    partial_func = partial(_surrounded_logic, graph)
    inp = []
    # Instead of exhaustively computing path length compute upper triangular distance matrix.
    # Depending on the case only 52% to 75% of the distance need to be computed.
    for s in range(len(hexes)):
        for t in range(s, len(hexes)):
            if s is not t:
                # Append the (source, target) tuples
                inp.append((hexes[s], hexes[t]))

    # Execute with several processes
    out = process_pool.map(partial_func, inp)
    # Turn into a square matrix
    adj_mat = squareform(np.array(out))
    # Truncate at a specified flag value
    adj_mat[adj_mat > 3e5] = 0
    # Make a graph from the truncated adjacency matrix
    qg = nx.from_numpy_matrix(adj_mat)
    # Count number of connected components.
    # If 1, at least a path exists between each allied stone.
    # If 0, at least one allied stone is surrounded.
    if len(list(nx.connected_components(qg))) > 1:
        return 1
    return 0
