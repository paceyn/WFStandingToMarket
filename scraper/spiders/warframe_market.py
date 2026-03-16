import scrapy

from datetime import datetime


class WarframeMarketSpider(scrapy.Spider):
    name = "warframe_market"
    allowed_domains = ["warframe.market"]
    custom_settings = {
        "ITEM_PIPELINES": {"scraper.pipelines.WarframeMarketPipeline": 300}
    }

    def __init__(self, items, **kwargs):
        self.items = items
        super().__init__(**kwargs)

    async def start(self):
        for item in self.items:
            yield scrapy.Request(
                f"https://api.warframe.market/v2/orders/item/{item.lower()}",
                cb_kwargs={"item": item},
            )

    def parse(self, response, item, **kwargs):
        data = response.json()["data"]

        output = {
            "time": datetime.now(),
            "item": item,
            "sell-ingame": [],
            "sell-offline": [],
            "buy-ingame": [],
            "buy-offline": [],
        }

        for listing in data:
            match (listing["type"] == "sell", listing["user"]["status"] == "ingame"):
                case (True, True):
                    output["sell-ingame"].append(int(listing["platinum"]))
                case (True, False):
                    output["sell-offline"].append(int(listing["platinum"]))
                case (False, True):
                    output["buy-ingame"].append(int(listing["platinum"]))
                case (False, False):
                    output["buy-offline"].append(int(listing["platinum"]))

        yield output
