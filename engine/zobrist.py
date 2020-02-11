import random


class ZobristHash:
    def __init__(self, graph):
        self.num_pieces = 2
        self.num_spaces = len(graph.nodes)
        self.table = dict()

        # Compute a number of random 64 bits keys based on the number of board positions and type of player pieces
        nodes = [*graph.nodes]
        for i in range(self.num_pieces):
            for node in nodes:
                self.table[i+1, node] = random.getrandbits(64)

    def hash(self, graph):
        h = 0
        nodes = [*graph.nodes]
        for node in nodes:
            owner = graph.nodes[node]['owner']
            # Check if a stone is occupying a cell.
            if not owner == -1:
                # If it is XOR the current has key value with that of the corresponding position.
                h = h ^ self.table[(owner, node)]
        return h