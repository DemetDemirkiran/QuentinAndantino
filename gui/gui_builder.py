import pygame
from gui.hex.map import Map
from gui.hex.render import RenderGrid, RenderFog, RenderUnits


class GameWindow:
    def __init__(self, disp_size, size, board=10):
        pygame.init()
        self.board_size = board
        self.hex_size = size
        self.disp_size = disp_size
        self.map = Map(size[0], size[1])
        self.display = pygame.display
        self.running = True
        self.grid = RenderGrid(self.map, radius=16)
        self.fog = RenderFog(self.map, radius=16)
        self.unit = RenderUnits(self.map, radius=16)
        self.window = None

    def _init_display(self):
        """
        Inititalizes the PyGame display
        :return:
        """
        self.window = self.display.set_mode(self.disp_size)
        self.display.flip()

    def to_dict(self):
        """
        When called returns a dictionary with all the information required to load the game state. Objets can't be
        pickled and are automatically instanced so they are not saved.
        :return:
        Dictionary containing class relevant data.
        """
        window_dict = dict()
        window_dict['board_size'] = self.board_size
        window_dict['hex_size'] = self.hex_size
        window_dict['disp_size'] = self.disp_size
        window_dict['running'] = self.running
        return window_dict

    def from_dict(self, window_dict):
        """
        Loading of this class is handled in the GameInstance Object.
        :param window_dict:
        :return:
        """
        pass

    def on_event(self, event):
        """
        PyGame event handler. Input events are processed and sent to the corresponding function.
        :param event: PyGame event (mouse click, key press, etc.)
        :return:
        Type of the event caught and either the cell or the function to execute.
        """
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            row, col = event.pos
            cell = self.unit.get_cell(row, col)
            return event.type, cell
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                return event.type, "save"
            if event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                return event.type, "load"
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                return event.type, "undo"

    def change_cell_color(self, cell, color):
        """
        Given a cell position change its color.
        :param cell: Tuple (x, y)
        :param color: PyGame color of a player
        :return:
        """
        self.map.fog[cell] = color
        self.draw_display()

    def draw_display(self, init=False):
        """
        Draws the display to represent changes in the game state.
        :param init: Whether it is being called for the first time or not.
        :return:
        """
        if init:
            self._init_display()
            self.window.fill(pygame.Color('white'))
            # True board is composed of many more hexes than visible. They are made opaque so the board more closely
            # resembles the Andantino board.
            # Turn 'off' the hexes
            for cell in list(self.map.cells()):
                self.map.fog[cell] = self.fog.OBSCURED
            # Turn 'on' the necessary hexes
            for i in range(7, 7 + self.board_size):
                for cell in list(self.map.line((i, 0), direction=0, length=self.board_size-1)):
                    self.map.fog[cell] = self.fog.VISIBLE
                for cell in list(self.map.line((i, 0), direction=1, length=self.board_size-1)):
                    self.map.fog[cell] = self.fog.VISIBLE
                for cell in list(self.map.line((i + self.board_size-1,
                                                (self.board_size-1)*2), direction=4, length=self.board_size-1)):
                    self.map.fog[cell] = self.fog.VISIBLE
                for cell in list(self.map.line((i + self.board_size-1,
                                                (self.board_size-1)*2), direction=3, length=self.board_size-1)):
                    self.map.fog[cell] = self.fog.VISIBLE
        self.grid.draw()
        self.fog.draw()
        self.window.blit(self.grid, (0, 0))
        self.window.blit(self.fog, (0, 0))
        self.display.update()

    def run(self):
        self._init_display()
        self.draw_display(True)
        # main loop
        while self.running:
            # event handling, gets all event from the event queue
            for event in pygame.event.get():
                event_out = self.on_event(event)
                yield event_out
