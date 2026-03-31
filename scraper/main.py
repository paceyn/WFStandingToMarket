from datetime import datetime, timedelta
import os
from statistics import mean, stdev
from sys import argv
from collections import Counter

from dotenv import load_dotenv
import json
import json_repair
import re
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

    samples = list(items.aggregate([{"$sample": {"size": 3}}]))
    messages = [
        {
            "role": "system",
            "content": """You are a MongoDB query expert and financial analyst specializing in work with marketplace data. You will receive a sample of documents from a database and an explanation of the data. You will receive a natural language query from the user describing what they want to analyze, and your job is to output a single valid pymongo aggregation pipeline (a list of dicts) that would answer the user's query effectively. 

            Fields:
            - name, faction, query (Identifiers. query is never relevant and should never be called)
            - standing (In-game item price. Scaled 1:10000)
            - scans (Array of scans of the market, containing the four arrays below)
              - sell-ingame, sell-offline, buy-ingame, buy-offline (Arrays of market listings in platinum)

            The purchasing power of an item is a platinum value divided by its standing price. Only use platinum / standing when asked for purchasing power.
            sell-ingame is the most accurate indicator of platinum price of the entries in scans. Ignore sell-offline, buy-ingame, and buy-offline unless absolutely necessary.
            Remember that sell-ingame is an array. It's multiple market listings. Also remember that scan is an array; it's multiple scans.
            
            Respond with only a valid pymongo pipeline to match the user's query. You work in Python, so make sure your query is a pymongo query specifically; just output a raw Python list of dicts. Do not send any markdown explaining the pipeline, just the raw pipeline itself so it can immediately be used. Only use field names as they are presented in the samples.""",
        },
        {
            "role": "user",
            "content": f"""Samples:
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

        message = llm_msg["content"].split("</think>")[-1].strip()
        response = re.findall(r"\[[\s\S]*\{[\s\S]*\}[\s\S]*\]", message)

        print(f"""LLM: {message}""")

        if response:
            pipeline = json_repair.loads(response[0])
            print(pipeline)

            try:
                results = list(items.aggregate(pipeline))
            except pymongo.errors.OperationFailure as e:
                print(f"PyMongo returned a faulty pipeline: {e}")
            else:
                for item in results:
                    print(item)
                    print(f"""- {item["name"]}""")

        messages.append({"role": "user", "content": input("You: ").strip()})
        messages.append({"role": "assistant", "content": "[{"})

    client.close()


if __name__ == "__main__":
    main()
