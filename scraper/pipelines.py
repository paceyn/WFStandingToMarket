# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

import os

import dotenv
import pymongo


class WarframeMarketPipeline:
    def open_spider(self):
        dotenv.load_dotenv()
        self.client = pymongo.MongoClient(
            os.getenv("DB"), server_api=pymongo.server_api.ServerApi("1")
        )
        self.db = self.client["marketscraper"]
        self.items = self.db["items"]

        self.operations = []

    def close_spider(self):
        if self.operations:
            self.items.bulk_write(self.operations, ordered=False)

        self.client.close()

    def process_item(self, item):
        adapter = ItemAdapter(item)
        name = item["item"]
        adapter.pop("item", None)

        self.operations.append(
            pymongo.UpdateOne({"item": name}, {"$addToSet": {"scans": adapter}})
        )

        return item


class WarframeWikiPipeline:
    def open_spider(self):
        dotenv.load_dotenv()
        self.client = pymongo.MongoClient(
            os.getenv("DB"), server_api=pymongo.server_api.ServerApi("1")
        )
        self.db = self.client["marketscraper"]
        self.items = self.db["items"]

        self.operations = []

    def close_spider(self):
        if self.operations:
            self.items.bulk_write(self.operations, ordered=False)

        self.client.close()

    def process_item(self, item):
        if item["query"] in [
            "sigils",
            "specter",
            "specter#syndicate_specters",
            "void_relic",
            "void_relics",
            "squad_health_restore",
            "squad_energy_restore",
            "squad_shield_restore",
            "squad_ammo_restore",
            "squad_health_restore_(large)",
            "squad_energy_restore_(large)",
            "squad_shield_restore_(large)",
            "squad_ammo_restore_(large)",
            "captura",
            "orbiter#stencils",
            "exilus_weapon_adapter",
            "emotes",
            "armor_(cosmetic)",
            "orbiter#decorations",
            "simulacrum",
            "vosfor",
            "asita_rakta_syandana",
            "sancti_syandana",
            "secura_syandana",
            "synoid_syandana",
            "telos_syandana",
            "vaykor_syandana",
        ]:
            raise DropItem(f"""{item["name"]} is on the item blacklist""")

        # They updated the name on this apparently so it doesn't scrape properly
        replacements = {"negation_armor": "negation_swarm"}

        item["query"] = item["query"].replace("&", "and").replace("'", "")

        if item["query"] in replacements.keys():
            item["query"] = replacements[item["query"]]

        self.operations.append(
            pymongo.UpdateOne(
                {"item": item["query"]},
                {
                    "$setOnInsert": {
                        "item": item["query"],
                        "name": item["name"],
                        "standing": item["price"],
                    },
                    "$addToSet": {"factions": item["faction"]},
                },
                upsert=True,
            ),
        )

        return item
