from configs import player_config


class Player:
    def __init__(self, number, types):
        _player_types = ['human', 'ai']
        self.number = number
        self.color = player_config['color_dict'][number]
        self.move_list = []
        self.hex_list = set()
        if types not in _player_types:
            raise TypeError('Wrong player type.')
        if types == 'ai':
            self.heuristic = player_config['heuristic'][int(self.number) - 1]
        self.type = types

    def to_dict(self):
        """
        When called returns a dictionary with all the information required to load the game state. Objects can't be
        pickled and are automatically instanced so they are not saved.
        :return:
        Dictionary containing class relevant data.
        """
        player_dict = dict()
        player_dict['number'] = self.number
        player_dict['color'] = self.color
        player_dict['move_list'] = self.move_list
        player_dict['hex_list'] = self.hex_list
        player_dict['heuristic'] = None if self.type == 'human' else self.heuristic
        player_dict['type'] = self.type
        return player_dict

    def from_dict(self, player_dict):
        """
        Set the object's attributes according to a pre-loaded dictionary.
        :param player_dict: Dictionary containing player attributes.
        :return:
        """
        self.number = player_dict['number']
        self.color = player_dict['color']
        self.heuristic = player_dict['heuristic']
        self.type = player_dict['type']