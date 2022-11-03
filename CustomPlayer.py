import wavelink


class CustomPlayer(wavelink.Player):
    def __int__(self):
        super().__init__()
        self.queue = wavelink.Queue()
