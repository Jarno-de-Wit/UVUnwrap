import re
import math

class PackingNode():
    """
    A class that contains the tools to make inter-dependent texture placements possible.
    The coordinate system used in this system has its origin in the bottom left, positive upwards to the right.
    For get_bound, the side enumeration is flipped due to getting one side is connected to setting the other side.
    """
    def __init__(self, size: tuple[float], scale: float = 1.0, align: str = "tl", *, texture = None, vert = None, hori = None, buffer: int = 0):
        self.size = size
        self.scale = scale
        self.align = align.lower()
        self.buffer = buffer # The buffer between different nodes / textures in pixels
        self.texture = texture # The texture bounds that the node exists in
        if texture is not None:
            self.texture.nodes.append(self)
        # The nodes that this node depends on for its position
        self.vert = vert
        self.hori = hori

        # The actual location data
        self.left = 0
        self.bottom = 0
        self.right = size[0]
        self.top = size[1]
        if vert is not None and hori is not None:
            self.calculate()

    def calculate(self):
        # Set-up all parameters for the positioning step
        self.set_bound(0, self.axis_dir(0), self.hori.get_bound(0, self.axis_dir(0)))
        self.set_bound(1, self.axis_dir(1), self.vert.get_bound(1, self.axis_dir(1)))

    @property
    def width(self):
        return self.size[0] * self.scale
    @property
    def height(self):
        return self.size[1] * self.scale

    def axis_dir(self, axis: int) -> int:
        """
        Returns the direcction of the alignment axis.
        If the alignment for the axis is bottom or left, direction is 0.
        If the alignment for the axis is top or right, the direction is 1.
        """
        if axis: # Vertical
            return "t" in self.align
        else: # Horizontal
            return "r" in self.align

    def get_bound(self, axis: int, direction: int, include_buffer: bool = True) -> int:
        """
        Gets the position of the specified bound
        """
        if axis: # Vertical boundary
            if direction: # Aligning to the top
                return self.bottom - self.buffer if include_buffer else self.bottom
            else:
                return self.top + self.buffer if include_buffer else self.top
        else:
            if direction: # Aligning to the right hand side
                return self.left - self.buffer if include_buffer else self.left
            else:
                return self.right + self.buffer if include_buffer else self.right
    def set_bound(self, axis: int, direction: int, value: int):
        """
        Sets the value of the specified bound, updating any linked bounds in the process
        """
        if axis: # Vertical alignment
            if direction: # Setting the bottom value
                self.top = value
                self.bottom = value - self.height
            else:
                self.bottom = value
                self.top = value + self.height
        else:
            if direction: # Setting the right value
                self.right = value
                self.left = value - self.width
            else:
                self.left = value
                self.right = value + self.width

    def has_overlap(self, other, axis: int) -> bool:
        if isinstance(other, TextureNode):
            if axis: # V
                return self.top > other.top and self.bottom < other.bottom
            else: # H
                return self.left < other.left and self.right > other.right
        elif isinstance(other, PackingNode):
            if axis: # Vertical overlap
                return self.top > other.bottom and self.bottom < other.top
            else: # Horizontal overlap
                return self.left < other.right and self.right > other.left
        elif isinstance(other, (tuple, list)):
            if axis:
                return self.top > other[1] and self.bottom < other[0]
            else:
                return self.left < other[1] and self.right > other[0]
        else: # Numeric value (float, int)
            if axis: # Vertical
                return self.top >= other >= self.bottom
            else:
                return self.left <= other <= self.right
    def collides(self, other):
        return self.has_overlap(other, 0) and self.has_overlap(other, 1)

    def __str__(self):
        return f"Node ({self.size[0]:.2f}, {self.size[1]:.2f})"

    def __repr__(self):
        return str(self)

    def printLayout(self):
        print(f"{' '*7}{self.top: >+7.1f}")
        print(f"{self.left: >+7.1f}{' '*7}{self.right: >+7.1f}")
        print(f"{' '*7}{self.bottom: >+7.1f}")


class TextureNode(PackingNode):
    def __init__(self, size: tuple[float], *, buffer: int = 0):
        super().__init__(size, texture = None, buffer = buffer)

        # Define the edges inverted, such that objects aligned to the Node will align to the correct edge
        self.right = 0
        self.top = 0
        self.left = size[0]
        self.bottom = size[1]

        self.nodes = [self]

    def reset(self):
        self.nodes = [self]

    def get_placements(self, size: tuple[int], scale: float = 1., align: str = "tl") -> dict[tuple[PackingNode], tuple[float]]:
        """
        Finds all valid placements that are aligned to existing nodes
        """
        placements = {}

        # Set-up all parameters for the positioning step
        self.align = align.lower() # Allows the use of self.axis_dir
        x_dir = self.axis_dir(0)
        y_dir = self.axis_dir(1)

        test_node = PackingNode(size, scale, align, texture = None)

        for y_node in self.nodes:
            y = y_node.get_bound(1, y_dir)
            test_node.set_bound(1, y_dir, y)
            for x_node in self.nodes:
                if not test_node.has_overlap(x_node, 1):
                    continue
                x = x_node.get_bound(0, x_dir)
                test_node.set_bound(0, x_dir, x)
                if any(test_node.collides(node) for node in self.nodes[1:]):
                    continue
                elif any(abs(x_ - x) < 1e-5 and abs(y_ - y) < 1e-5 for x_, y_ in placements.values()): # Prevent repeated placements
                    continue
                placements[(x_node, y_node)] = (x, y)

        return placements

    def get_placement(self, size: tuple[int], scale: float = 1., align: str = "tl"):
        """
        Returns the "optimal" placement for a rectangle with a given size
        """
        placements = self.get_placements(size, scale, align)
        try:
            return min(placements.items(), key = lambda place: math.sqrt(place[1][0]**2 + place[1][1]**2))
        except:
            return None

    def __str__(self):
        return f"Texture node ({self.size[0]}, {self.size[1]})"
