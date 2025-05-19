import os

import pymongo

from WhiteoutSurvival.models.alliance import Alliance


class AllianceRepository:
    def __init__(self, guild_id):
        self.client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[guild_id]["whiteout_survival"]
        self.alliances = self.db["alliances"]

    def save(self, alliance: Alliance) -> Alliance:
        """ Save the player to the database. """
        self.alliances.update_one(
            {"id": alliance.id},
            {"$set": alliance.model_dump()},
            upsert=True,
        )

        return alliance

    def get(self, id: int) -> Alliance:
        """ Get the player from the database.
        :param id: The ID of the player to get.
        :return: The player object if found, None otherwise.
        """
        alliance_data = self.alliances.find_one({"id": id})
        if alliance_data:
            return Alliance(**alliance_data)
        return None
