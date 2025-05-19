import os

import pymongo

from WhiteoutSurvival.models.player import Player


class PlayerRepository:
    def __init__(self, guild_id):
        self.client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[guild_id]["whiteout_survival"]
        self.players = self.db["players"]

    def save(self, player: Player) -> Player:
        """ Save the player to the database. """
        self.players.update_one(
            {"id": player.id},
            {"$set": player.model_dump()},
            upsert=True,
        )

        return player

    def get(self, id: int) -> Player:
        """ Get the player from the database.
        :param id: The ID of the player to get.
        :return: The player object if found, None otherwise.
        """
        player_data = self.players.find_one({"id": id})
        if player_data:
            return Player(**player_data)
        return None
