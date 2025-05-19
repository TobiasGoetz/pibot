from pydantic import BaseModel


class Alliance(BaseModel):
    """ Class representing an alliance in the game. """

    state: int
    tag: str
    name: str | None = None
    r5_ids: list[int]
    r4_ids: list[int] | None = None
    r3_ids: list[int] | None = None
    r2_ids: list[int] | None = None
    r1_ids: list[int] | None = None
