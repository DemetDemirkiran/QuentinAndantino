import os
import pickle
import time
from itertools import chain
from time import sleep
import h5py
from configs import *
from engine.game_engine import GameEngine
from engine.player import Player
from gui.gui_builder import GameWindow


class GameInstance:
    def __init__(self):
        self.player1 = Player('1', player_config['types'][0])
        self.player2 = Player('2', player_config['types'][1])
        self.game_board = GameWindow(window_config['resolution'], window_config['size'], window_config['hexes'])
        self.game_board.draw_display(True)
        self.game_engine = GameEngine(self.game_board, self.player1)
        self.turns_played = 0
        # Four functions for four different types of game.
        self._games = {
            'human_human': self._run_p1_p2_human,
            'human_ai': self._run_p1_human_p2_ai,
            'ai_human': self._run_p1_ai_p2_human,
            'ai_ai': self._run_p1_ai_p2_ai,
        }
        # Select game type based on players
        self._run_func = self._games['{}_{}'.format(self.player1.type, self.player2.type)]
        self.game_ended = False
        self.start_time = time.time()

    def _save_state(self):
        """
        Saving function. Calls the 'to_dict' function of each object and stores it as a pickle file.
        :return:
        """
        save_path = os.path.join(save_config['root_dir'], str(time.time())+'.pkl')
        save_dict = dict()
        save_dict['player1'] = self.player1.to_dict()
        save_dict['player2'] = self.player2.to_dict()
        save_dict['game_board'] = self.game_board.to_dict()
        save_dict['game_engine'] = self.game_engine.to_dict()
        save_dict['turns_played'] = self.turns_played
        save_dict['_run_func'] = '{}_{}'.format(self.player1.type, self.player2.type)
        save_dict['game_ended'] = self.game_ended
        save_dict['start_time'] = self.start_time
        with open(save_path, 'wb') as f:
            pickle.dump(save_dict, f)

    def _load_state(self):
        """
        Loads from the checkpoint specified in configs. This is done by re-playing both players moves in the right
        sequence. Board must be empty for correct loading.
        :return:
        """
        load_path = os.path.join(save_config['load_from'])
        with open(load_path, 'rb') as f:
            save_dict = pickle.load(f)
        self.player1.from_dict(save_dict['player1'])
        self.player2.from_dict(save_dict['player2'])
        self.game_engine.from_dict(save_dict['game_engine'])
        self._run_func = self._games[save_dict['_run_func']]
        # Chain the moves in the right order and iterate through
        for move in [*chain.from_iterable(zip(save_dict['player1']['move_list'], save_dict['player2']['move_list']))]:
            self.play_piece(move)

        self.game_ended = save_dict['game_ended']
        self.start_time = save_dict['start_time']

    def _undo_move(self):
        """
        Removes the last two played stones.
        :return:
        """
        # Undo player's move
        player = self.player1 if self._get_turn() == 1 else self.player2
        if len(player.move_list) > 0:
            last_move = player.move_list.pop(-1)
            player.hex_list.remove(last_move)
            # Sanity check
            if not len(player.hex_list) == len(player.move_list):
                raise ValueError('List and set have different element count')
            self.game_engine.set_owner(last_move, -1)
            self.game_board.change_cell_color(last_move, (255, 255, 255, 255))
            self.turns_played -= 1

            # Then undo AI's move
            player = self.player1 if self._get_turn() == 1 else self.player2
            last_move = player.move_list.pop(-1)
            player.hex_list.remove(last_move)
            # Sanity check
            if not len(player.hex_list) == len(player.move_list):
                raise ValueError('List and set have different element count')
            self.game_engine.set_owner(last_move, -1)
            self.game_board.change_cell_color(last_move, (255, 255, 255, 255))
            self.turns_played -= 1

    def _human_move(self):
        """
        Function handling human-made plays. Validates if the move is possible then changes the cell color and updates
        the player move list. Also handles other commands (save, load, undo).
        :return:
        """
        for event in pygame.event.get():
            event_out = self.game_board.on_event(event)
            if event_out is not None:
                data = event_out[1]
                event_out = event_out[0]
                if event_out == pygame.MOUSEBUTTONDOWN:
                    if not self.game_ended:
                        self.play_piece(data)
                elif event_out == pygame.KEYDOWN:
                    if data == 'save':
                        self._save_state()
                    elif data == 'load':
                        self._load_state()
                    elif data == 'undo':
                        self._undo_move()

    def _run_p1_p2_human(self):
        """
        Runs a human vs. human game.
        :return:
        """
        # event handling, gets all event from the event queue
        self._human_move()

    def _run_p1_human_p2_ai(self):
        """
        Runs a human vs. ai game.
        :return:
        """
        if self._get_turn() == 0:
            self._human_move()
        else:
            if not self.game_ended:
                move = self.game_engine.ai_move(self.player1.hex_list,
                                                self.player2.hex_list,
                                                self.player2.heuristic)
                self.play_piece(move)

    def _run_p1_ai_p2_human(self):
        """
        Runs an ai vs. human game.
        :return:
        """
        if self._get_turn() == 1:
            self._human_move()
        else:
            if not self.game_ended:
                move = self.game_engine.ai_move(self.player1.hex_list,
                                                self.player2.hex_list,
                                                self.player1.heuristic)
                self.play_piece(move)

    def _run_p1_ai_p2_ai(self):
        """
        Runs an ai vs. ai game. Alternates between each player's evaluation function.
        :return:
        """
        if not self.game_ended:
            if self.turns_played % 2 == 0:
                heuristic_type = self.player1.heuristic
            else:
                heuristic_type = self.player2.heuristic
            move = self.game_engine.ai_move(self.player1.hex_list,
                                            self.player2.hex_list,
                                            heuristic_type)
            self.play_piece(move)
            sleep(1)
            pygame.event.get()

    def _check_if_open(self, cell):
        """
        Check if a cell does not contain a stone.
        :param cell: Tuple (x,y).
        :return:
        True if the cell is empty. False otherwise.
        """
        if cell not in self.player1.hex_list and cell not in self.player2.hex_list:
            return True
        else:
            return False

    def _check_if_playable(self, cell):
        """
        Cell is playable if adjacent to two other cells.
        :param cell: Tuple (x,y).
        :return:
        Number of neighbours.
        """
        hex_p1 = self.player1.hex_list
        hex_p2 = self.player2.hex_list
        hex_played = set(hex_p1).union(hex_p2)

        neigh_cell = set(self.game_board.map.spread(cell))
        hex_count = hex_played.intersection(neigh_cell)
        return len(hex_count)

    def _check_cell(self, cell):
        """
        Validate if cell is playable.
        :param cell: Coordinates of cell to check
        :param player_cells: List of cells marked by a player token.
        :return:
        True if cell is surrounded by 2 or more pieces.
        """

        if self._check_if_playable(cell) >= 2:
            return True
        return False

    def _add(self, cell, player):
        """
        GUI and backend management of plays without validity checks. Change the hex color. Set owner in board graph.
        Add move to correct player. Increment turn counter.
        :param cell: Tuple (x,y).
        :param player:
        :return:
        """
        self.game_board.change_cell_color(cell, player.color)
        self.game_engine.set_owner(cell, player.number)
        player.hex_list.add(cell)
        player.move_list.append(cell)
        self.turns_played += 1

    def _check_and_add(self, cell, player):
        """
        GUI and backend management of plays without validity checks. Change the hex color. Set owner in board graph.
        Add move to correct player. Increment turn counter. Check if game has ended.
        :param cell: Tuple (x,y).
        :param player:
        :return:
        """
        # Check for validity of the move
        if self._check_cell(cell):
            self.game_board.change_cell_color(cell, player.color)
            self.game_engine.set_owner(cell, player.number)
            player.hex_list.add(cell)
            player.move_list.append(cell)
            self.turns_played += 1

        # If a few plays have been made start checking for game end.
        if len(self.player1.hex_list) >= 2 or len(self.player2.hex_list) >= 2:
            result = []
            surrounded1, colinear1, surrounded2, colinear2 = self.game_engine.check_for_game_end(self.player1.hex_list,
                                                                                                 self.player2.hex_list,
                                                                                                 details=True)
            p0_won = surrounded1 or colinear1
            p1_won = surrounded2 or colinear2
            # Print message based on game result
            if p0_won:
                print("Player 1 has won!")
                result = (1, surrounded1, colinear1)
                self.game_ended = p0_won

            elif p1_won:
                print("Player 2 has won!")
                result = (2, surrounded2, colinear2)
                self.game_ended = p1_won

            elif p0_won and p1_won or (len(self.player1.hex_list) + len(self.player2.hex_list)) >= 50:
                print("Draw!")
                result = (0, -1, -1)
                self.game_ended = 1

            # Save a small log file
            if self.game_ended:
                end_time = time.time() - self.start_time
                print("Game finished in {} seconds".format(end_time))
                with h5py.File(os.path.join(save_config['root_dir'], 'log_{}.h5'.format(time.time())), 'w') as game_log:
                    sess_id = str(len(game_log.keys()))
                    session_log = game_log.create_group(sess_id)
                    session_log.create_dataset(name='win', data=result)
                    session_log.create_dataset(name='time', data=end_time)

                    p1_log = session_log.create_group('p1')
                    if self.player1.type == 'ai':
                        p1_log.create_dataset(name='heuristic', data=self.player1.heuristic)
                    p1_log.create_dataset(name='surrounded', data=surrounded1)
                    p1_log.create_dataset(name='colinear', data=colinear1)

                    p2_log = session_log.create_group('p2')
                    if self.player2.type == 'ai':
                        p2_log.create_dataset(name='heuristic', data=self.player2.heuristic)
                    p2_log.create_dataset(name='surrounded', data=surrounded2)
                    p2_log.create_dataset(name='colinear', data=colinear2)
                self.game_board.running = False

    def add_piece(self, cell, first=False):
        """
        Add a stone on the board. No check if first pieces. Validity check afterwards.
        :param cell: Tuple (x,y).
        :param first: First turn or not
        :return:
        """
        if self._get_turn() == 0:
            self._add(cell, self.player1) if first else self._check_and_add(cell, self.player1)
        else:
            self._add(cell, self.player2) if first else self._check_and_add(cell, self.player2)

    def _check_if_first_piece(self, cell):
        """
        First piece must be played in the center of the board. HARDCODED for current board.
        :param cell:
        :return:
        """
        # Center cell for standard board. Hardcoded
        center_cell = (16, 9)
        if self.turns_played == 0:
            center_nn = set(self.game_board.map.spread(center_cell, radius=1))
        else:
            center_nn = set(self.game_board.map.spread(center_cell, radius=1))
            player1_nn = set(self.game_board.map.spread(self.player1.move_list[0], radius=1))
            center_nn = center_nn.intersection(player1_nn)
        if cell in center_nn and self._check_if_open(cell):
            self.add_piece(cell, True)

    def _get_turn(self):
        """
        :return:
        Returns which player should make a move.
        """
        return self.turns_played % 2

    def play_piece(self, cell):
        """
        Play a stone in a hex. Performa all validity checks.
        :param cell: Tuple (x,y).
        :return:
        """
        if len(self.player1.move_list) == 0:
            self._check_if_first_piece(cell)
        elif len(self.player1.move_list) > 0 and len(self.player2.move_list) == 0:
            self._check_if_first_piece(cell)
        elif self._check_if_open(cell):
            self.add_piece(cell)

    def run(self):
        # main loop
        while self.game_board.running:
            self._run_func()
        if not self.game_board.running:
            "Save a capture of the final board state"
            pygame.image.save(self.game_board.window, os.path.join(save_config['root_dir'],
                                                                   "screenshot{}.jpg".format(time.time())))


if __name__ == "__main__":
    game = GameInstance()
    game.run()
