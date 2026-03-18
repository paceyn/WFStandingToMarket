from datetime import datetime, timedelta
import os
from statistics import mean, stdev
from sys import argv
from collections import Counter

from dotenv import load_dotenv
import pymongo
from multiprocessing import Process
import ollama


def crawl_wiki():
    from spiders.warframe_wiki import WarframeWikiSpider

    from scrapy.crawler import AsyncCrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = AsyncCrawlerProcess(settings=get_project_settings())
    process.crawl(WarframeWikiSpider)
    process.start()


def crawl_market(item_names):
    from spiders.warframe_market import WarframeMarketSpider

    from scrapy.crawler import AsyncCrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = AsyncCrawlerProcess(settings=get_project_settings())
    process.crawl(WarframeMarketSpider, items=item_names)
    process.start()


def main():
    load_dotenv()
    client = pymongo.MongoClient(
        os.getenv("DB"), server_api=pymongo.server_api.ServerApi("1")
    )
    db = client["marketscraper"]

    if "items" not in db.list_collection_names():
        wiki_process = Process(target=crawl_wiki)
        wiki_process.start()
        wiki_process.join()

    items = db["items"]

    item_names = items.distinct(
        "item",
        {
            "factions": {
                "$in": [
                    "Steel Meridian",
                    "Arbiters of Hexis",
                    "Cephalon Suda",
                    "The Perrin Sequence",
                    "Red Veil",
                    "Cephalon Suda",
                ]
            }
        },
    )

    if "-s" in argv:
        market_process = Process(target=crawl_market, args=(item_names,))
        market_process.start()
        market_process.join()

    item_details = {}

    for name in item_names:
        item = items.find_one({"item": name})

        # For faction filtering. Hardcoded for now
        valid_factions = [
            "Steel Meridian",
            "Arbiters of Hexis",
            "Cephalon Suda",
            "The Perrin Sequence",
            "Red Veil",
            "Cephalon Suda",
        ]

        if not any(i in valid_factions for i in item["factions"]):
            continue

        if "scans" not in item.keys():
            continue

        latest = sorted(list(item["scans"]), key=lambda x: x["time"])[-1]

        # So math doesn't break
        if not latest["sell-ingame"]:
            latest["sell-ingame"].append(0)
            latest["sell-ingame"].append(0)
        if not latest["sell-offline"]:
            latest["sell-offline"].append(0)
            latest["sell-offline"].append(0)
        if not latest["buy-ingame"]:
            latest["buy-ingame"].append(0)
            latest["buy-ingame"].append(0)
        if not latest["buy-offline"]:
            latest["buy-offline"].append(0)
            latest["buy-offline"].append(0)

        count = Counter(latest["sell-ingame"])

        for k, v in sorted(list(count.items()), key=lambda x: x[0]):
            if v <= 1:
                count.pop(k)
            break

        metric = latest["sell-ingame"]

        average = mean(metric)
        stddev = stdev(metric)

        item_details[item["name"]] = {
            "standing": item["standing"],
            "plat_min": min(metric),
            "plat_min_adjusted": min(count.keys()),
            "average": average,
            "average_stdev": mean(
                [
                    x
                    for x in latest["sell-ingame"]
                    if average - stddev <= x and x <= average + stddev
                ]
            ),
        }

    for k, v in sorted(
        list(item_details.items()), key=lambda x: -x[1]["plat_min"] / x[1]["standing"]
    ):
        print(
            f"{k} - {v['plat_min'] / v['standing']}p per 10k standing ({round(v['average_stdev']) / v['standing']}p against the average)"
        )

    print("---")

    print("Sorted by minimum bid:")
    for k, v in sorted(
        list(item_details.items()), key=lambda x: -x[1]["plat_min"] / x[1]["standing"]
    )[:10]:
        print(f"{k} - {v['plat_min'] / v['standing']:.1f}p/10k")

    print("---")

    print("Sorted by minimum bid minus undersellers:")
    for k, v in sorted(
        list(item_details.items()),
        key=lambda x: -x[1]["plat_min_adjusted"] / x[1]["standing"],
    )[:10]:
        print(f"{k} - {v['plat_min_adjusted'] / v['standing']:.1f}p/10k")

    print("---")

    print("Sorted by average:")
    for k, v in sorted(
        list(item_details.items()), key=lambda x: -x[1]["average"] / x[1]["standing"]
    )[:10]:
        print(f"{k} - {v['average'] / v['standing']:.1f}p/10k")

    print("---")

    print("Sorted by average of bids within 1 stdev:")
    for k, v in sorted(
        list(item_details.items()),
        key=lambda x: -x[1]["average_stdev"] / x[1]["standing"],
    )[:10]:
        print(f"{k} - {v['average_stdev'] / v['standing']:.1f}p/10k")

    samples = list(items.aggregate([{"$sample": {"size": 8}}]))
    messages = [
        {
            "role": "system",
            "content": "You are a financial analyst with experience reading MongoDB databases.",
        },
        {
            "role": "user",
            "content": f"""The following are scans of a Warframe marketplace for items with a faction with various sets of listings taken from across various points in time. The important points here are the standing, representing how expensive the item is in in-game currency, and the prices in the most recent scan, showing all of the trades on the market as of the last time scanned; personally, I consider sell-ingame the most reliable data to analyze, but there might be more to factor in. Summarize any key insights about the documents provided and the dataset at large, then give me the necessary information to perform such queries; I want to understand the best way to analyze the data and figure out what the best items to invest in are, as the data seems quite sporadic. Afterwards, please perform market analysis on the data given yourself.
    
    Documents:
    {samples}""",
        },
    ]

    while True:
        response = ollama.chat(
            model="qwen3:8b",
            messages=messages,
        )

        llm_msg = response["message"]
        messages.append(llm_msg)
        print(f"LLM: {llm_msg['content']}")

        messages.append({"role": "user", "content": input("You: ").strip()})

    client.close()


if __name__ == "__main__":
    main()
