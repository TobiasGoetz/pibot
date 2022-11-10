import wavelink


class Player(wavelink.Player):
    def __int__(self):
        super().__init__()
        self.queue = wavelink.Queue()
