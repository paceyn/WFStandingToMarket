import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import unquote


class WarframeWikiSpider(scrapy.Spider):
    name = "warframe_wiki"
    allowed_domains = ["wiki.warframe.com"]
    custom_settings = {
        "ITEM_PIPELINES": {"scraper.pipelines.WarframeWikiPipeline": 300}
    }

    async def start(self):
        for faction in [
            "Steel_Meridian",
            "Arbiters_of_Hexis",
            "Cephalon_Suda",
            "The_Perrin_Sequence",
            "Red_Veil",
            "New_Loka",
        ]:
            yield scrapy.Request(
                f"https://wiki.warframe.com/w/{faction}",
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod(
                            "eval_on_selector",
                            f'.mw-customtoggle-{faction.replace("_", "")}',
                            "el => el.scrollIntoView()",
                        ),
                        PageMethod(
                            "click", f'.mw-customtoggle-{faction.replace("_", "")}'
                        ),
                        PageMethod(
                            "wait_for_selector",
                            f'#mw-customcollapsible-{faction.replace("_", "")}',
                        ),
                        PageMethod(
                            "evaluate", "window.scrollTo(0, document.body.scrollHeight)"
                        ),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
                cb_kwargs={"faction": faction},
            )

    def parse(self, response, faction, **kwargs):
        table = response.css(
            f'#mw-customcollapsible-{faction.replace("_", "")} > div > *'
        )

        for item in table:
            price = int(item.css("p > span::text").get().replace(",", "")) / 10000
            href_name = (
                unquote(item.css("div > a::attr(href)").get().split("/")[2])
                .replace("&", "and")
                .replace("'", "")
            )
            name = item.css("div > a > span::text").get()

            if href_name in [
                "Corvas",
                "Velocitus",
                "Kaszas",
                "Decurion",
                "Phaedra",
                "Rathbone",
                "Onorix",
                "Cyngas",
                "Centaur",
                "Fluctus",
                "Agkuza",
            ]:
                query = name.replace(" ", "_").lower()
            else:
                query = href_name.lower()

            yield {
                "faction": faction.replace("_", " "),
                "name": name,
                "query": query,
                "price": price,
            }
