from abc import ABCMeta, abstractmethod
import pygame
import math
from gui.hex.map import Grid
from gui.hex.map import Map, MapUnit
import numpy as np

# Hex drawing and management code found at: https://github.com/aestrivex/pygame-hex-grid

SQRT3 = math.sqrt(3)

class Render( pygame.Surface ):
    __metaclass__ = ABCMeta
    def __init__( self, map, radius=5, *args, **keywords ):
        self.map = map
        self.radius = radius
        # Colors for the map
        self.GRID_COLOR = pygame.Color(50, 50, 50)

        super(Render, self).__init__((self.width, self.height), *args, **keywords)
        self.cell = [(.5 * self.radius, 0),
                     (1.5 * self.radius, 0),
                     (2 * self.radius, SQRT3 / 2 * self.radius),
                     (1.5 * self.radius, SQRT3 * self.radius),
                     (.5 * self.radius, SQRT3 * self.radius),
                     (0, SQRT3 / 2 * self.radius)]

    @property
    def width(self):
        return self.map.cols * self.radius * 1.5 + self.radius / 2.0
    @property
    def height(self):
        return (self.map.rows + .5) * self.radius * SQRT3 + 1

    def get_surface( self,  row, col):
        """
        :param row:
        :param col:
        :return:
        Returns a subsurface corresponding to the surface, hopefully with trim_cell wrapped around the blit method.
		"""
        width = 2 * self.radius
        height = self.radius * SQRT3

        top = (row - math.ceil(col / 2.0)) * height + ( height / 2 if col % 2 == 1 else 0)
        left = 1.5 * self.radius * col
        return self.subsurface(pygame.Rect(left, top, width, height))

    # Draw methods
    @abstractmethod
    def draw( self ):
        """
		An abstract base method for various render objects to call to paint
		themselves.  If called via super, it fills the screen with the colorkey,
		if the colorkey is not set, it sets the colorkey to magenta (#FF00FF)
		and fills this surface.
		"""
        color = self.get_colorkey()
        if not color:
            magenta = pygame.Color(255, 0, 255)
            self.set_colorkey( magenta )
            color = magenta
        self.fill( color )

    # Identify cell
    def get_cell( self, y, x):
        """
        :param x:
        :param y:
        :return:
        Identify the cell clicked in terms of row and column
		"""
        # Identify the square grid the click is in.
        row = math.floor( y / ( SQRT3 * self.radius ) )
        col = math.floor( x / ( 1.5 * self.radius ) )

        # Determine if cell outside cell centered in this grid.
        x = x - col * 1.5 * self.radius
        y = y - row * SQRT3 * self.radius

        # Transform row to match our hex coordinates, approximately
        row = row + math.floor( ( col + 1 ) / 2.0 )

        # Correct row and col for boundaries of a hex grid
        if col % 2 == 0:
            if 	y < SQRT3 * self.radius / 2 and x < .5 * self.radius and \
                            y < SQRT3 * self.radius / 2 - x:
                row, col = row - 1, col - 1
            elif y > SQRT3 * self.radius / 2 and x < .5 * self.radius and \
				y > SQRT3 * self.radius / 2 + x:
                row, col = row, col - 1
        else:
            if 	x < .5 * self.radius and abs( y - SQRT3 * self.radius / 2 ) < SQRT3 * self.radius / 2 - x:
                row, col = row - 1 , col - 1
            elif y < SQRT3 * self.radius / 2:
                row, col = row - 1, col

        return ( row, col ) if self.map.valid_cell( ( row, col ) ) else None

    def fit_window( self, window ):
        top = max( window.get_height() - self.height, 0 )
        left = max( window.get_width() - map.width, 0 )
        return ( top, left )

class RenderUnits( Render ):
    """
	A premade render object that will automatically draw the Units from the map
	"""

    def __init__( self, map, *args, **keywords ):
        super( RenderUnits, self ).__init__( map, *args, **keywords )
        if not hasattr( self.map, 'units' ):
            self.map.units = Grid()

    def draw(self):
        """
		Calls unit.paint for all units on self.map
		"""
        super( RenderUnits, self ).draw()
        units = self.map.units

        for position, unit in units.items():
            row, col = position
            surface = self.get_surface(row, col)
            unit.paint(surface)

class RenderGrid( Render ):
    def draw( self ):
        """
		Draws a hex grid, based on the map object, onto this Surface
		"""
        super( RenderGrid, self ).draw()
        # A point list describing a single cell, based on the radius of each hex
        for col in range( self.map.cols ):
            # Alternate the offset of the cells based on column
            offset = self.radius * SQRT3 / 2 if col % 2 else 0
            for row in range( self.map.rows ):
                # Calculate the offset of the cell
                top = offset + SQRT3 * row * self.radius
                left = 1.5 * col * self.radius
                # Create a point list containing the offset cell
                points = [(y + top,  x + left) for (x, y) in self.cell]
                # Draw the polygon onto the surface
                pygame.draw.polygon(self, self.GRID_COLOR, points, 1)


class RenderFog( Render ):

    OBSCURED = pygame.Color(0, 0, 0, 255)
    SEEN = pygame.Color(0, 0, 0, 100)
    VISIBLE = pygame.Color(0, 0, 0, 0)
    RED = pygame.Color('red')
    GREEN = pygame.Color('green')
    BLUE = pygame.Color('blue')

    def __init__(self, map, *args, **keywords):
        super(RenderFog, self).__init__(map, *args, flags=pygame.SRCALPHA, **keywords)
        if not hasattr(self.map, 'fog'):
            self.map.fog = Grid(default=self.OBSCURED)
            self.rects = pygame.sprite.Group()

    def draw(self):
        #Some constants for the math
        height = self.radius * SQRT3
        width = 1.5 * self.radius
        offset = height / 2
        self.fill(self.OBSCURED)
        for cell in self.map.cells():
            row, col = cell
            surface = self.get_cell(row, col)

            # Calculate the position of the cell
            top = row * height - offset * col
            left = width * col

            #Determine the points that corresponds with
            points = [(y + top, x + left) for (x, y) in self.cell]
            # Draw the polygon onto the surface
            pygame.draw.polygon(self, self.map.fog[cell], points, 0)
            # Here for cellID text
            # new_center = points[0] + np.abs(np.array(points[0]) - np.array(points[3])) / 2
            # rect = Text(self, new_center[0], new_center[1], 15, 15, '{},{}'.format(row, col))
            # self.rects.add(rect)


def trim_cell(surface):
    pass


class Text(pygame.sprite.Sprite):

    def __init__(self, screen, x, y, width, height, text):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 0, 0))
        self.image.set_colorkey((255, 0, 0))
        self.font = pygame.font.SysFont('arial', 20)
        self.text = self.font.render('{}'.format(text), True, (0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        screen.blit(self.text, self.rect)

class Unit(MapUnit):

    color = pygame.Color('red')

    def paint(self, surface):
        font = pygame.font.SysFont('arial', 20)
        text = font.render('@', True, (0, 0, 255, 255))
        rect = text.get_rect()
        rect.center = (640, 480)
        surface.blit(text, rect)
        # pygame.draw.circle(surface, self.color, (int(radius), int(SQRT3 / 2 * radius)), int(radius - radius * .3 ))

if __name__ == '__main__':

    import sys
    m = Map(30, 30)

    grid = RenderGrid( m, radius=32 )
    units = RenderUnits( m, radius=32 )
    fog = RenderFog( m, radius=32 )



    cells = list(m.cells())
    for cell in cells:
        m.fog[cell] = fog.OBSCURED

    for i in range(5+2, 15+2):
        for cell in list(m.line((i,0), direction=0, length=9)):
            m.fog[cell] = fog.VISIBLE
        for cell in list(m.line((i, 0), direction=1, length=9)):
            m.fog[cell] = fog.VISIBLE
        for cell in list(m.line((i+9, 18), direction=4, length=9)):
            m.fog[cell] = fog.VISIBLE
        for cell in list(m.line((i+9, 18), direction=3, length=9)):
            m.fog[cell] = fog.VISIBLE

    m.fog[7, 7] = fog.RED
    m.fog[9, 7] = fog.BLUE
    m.fog[7, 9] = fog.GREEN

    print(m.ascii())


    try:
        pygame.init()
        fpsClock = pygame.time.Clock()

        window = pygame.display.set_mode((640*2, 480*2), 1)
        from pygame.locals import QUIT, MOUSEBUTTONDOWN

        #Leave it running until exit
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    row, col = event.pos
                    print(units.get_cell(row, col ))

            window.fill(pygame.Color( 'white' ))
            grid.draw()
            units.draw()
            fog.draw()
            window.blit( grid, ( 0, 0 ) )
            window.blit( units, ( 0, 0 ) )
            window.blit( fog, ( 0, 0 ) )
            pygame.display.update()
            fpsClock.tick( 10 )
    finally:
        pygame.quit()