"""
Custom Wavelink Player
"""
import wavelink


class Player(wavelink.Player):
    """
    Custom Wavelink Player
    """
    def __int__(self):
        super().__init__()
        self.queue = wavelink.Queue()
