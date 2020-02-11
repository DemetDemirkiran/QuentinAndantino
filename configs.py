import pygame

# Configuration file. Modify it to change the program's behavior like player order, evaluation function, etc.
# Be aware hex starting positions are hard-coded so the 'hexes' parameter SHOULD NOT be changed.
window_config = {
    'resolution': (640, 480),
    'size': (30, 30),
    'hexes': 10
}

player_config = {
    'color_dict': {
    '1': pygame.Color('red'),
    '2': pygame.Color('blue')},
    'types': ('human', 'ai'),
    'heuristic': ('hex_heuristic', 'hex_heuristic')
}

save_config = {
    'root_dir': "D:\\PycharmProjects\\andantino_logs",
    'load_from': 'D:\\PycharmProjects\\andantino_logs\\1580046226.547153.pkl'
}
