from pydantic import BaseModel


class Player(BaseModel):
    """ Class representing a player in the game. """

    id: int
    name: str
    state: int | None = None

    furnace_level: int | None = None
    power: int | None = None
