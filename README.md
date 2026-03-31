# WFStandingToMarket
Better informing players on where to spend Warframe faction standing to get the most out of trading

This web scraper first scrapes the wiki and populates a MongoDB collection with a document for each of the items of each of the game's six faction syndicates, manually filtered based on whether the items can be traded, then scrapes the warframe.market API to create a timestamped list of prices that is added to the corresponding items' documents. The program then sorts through the data and displays the prices of items sorted by minimum in-game sell listing minus any single listing undersells (removing the first entry if it is the only one of its price, as players underselling items like this has led to weird results in the past), as well as a short list of the top items as sorted by various metrics in order to account for variation in the data the warframe.market API exposes. The program focuses on the most recent scans of the market and specifically looks at the purchasing power of items by the given platinum prices alone, focusing on what can be listed on the market immediately after purchasing, as this tends to be the most common use case for trading faction items.

The project is powered by ScraPy, using its Playwright integration to scrape the wiki, and MongoDB. Playwright interfaces well with a React Native web application like the Warframe wiki, a convenient tool that interfaces well with a more flexible library like ScraPy and means I don't need to interface with something entirely seperate just to get the market listings, while working with lists in MongoDB means I don't need to create an extra collection for the scans that's ultimately harder to sort through, making it a good fit given my previous experience with it. The database tracks around 250 documents, including preserved scans of the market from various points in time that may hold listings in the hundreds.

I'm currently focusing my efforts on an additional branch featuring Ollama integration, curating a default prompt and an interactive interface for the end of the file to act as a lightweight market analyst with MongoDB integration. Users should be able to ask questions like "What items are traded at an above-average price for their standing?" or "Which items show high value and high listing volume?" and receive structured, data-driven responses.

# Usage
- Install uv and call `uv sync` in the directory, or use any other form of Python virtual environment generator that can parse the pyproject.toml.
- Create a `.env` file with the line `DB=[MongoDB URI]`. A MongoDB Atlas development database has been good in my use so far. At this point, I also recommend placing a user agent in the `settings.py` file.
- Install `ollama` to your system. Open it up and install the model `qwen2.5-coder:14b` (or an alternative of your choice if you choose to modify the code). You can close it afterwards.
- Run `uv run main.py -s`, or source the virtual environment and run the program through Python normally. The wiki will be scraped if the table doesn't exist in the database, with the market being scraped only being entered if the `-s` flag is used in the future. If you just want to see the results without running the scraper on the market again, just run `uv run main.py`.

# Sample output
Excludes the primary first list. Taken from a scan of the market on 03/20/26.
```
Sorted by minimum bid:
Duality (Equinox) - 8.0p/10k
Entropy Detonation (Obex) - 7.6p/10k
Endless Lullaby (Baruuk) - 7.2p/10k
Piercing Navigator (Ivara) - 7.2p/10k
Resonating Quake (Banshee) - 7.2p/10k
Savage Silence (Banshee) - 7.2p/10k
Tidal Impunity (Hydroid) - 7.2p/10k
Corvas Barrel - 7.0p/10k
Cyngas Receiver - 7.0p/10k
Fluctus Barrel - 7.0p/10k
---
Sorted by minimum bid minus undersellers:
Toxic Sequence (Acrid) - 18.0p/10k
Entropy Detonation (Obex) - 16.0p/10k
Corvas Barrel - 10.0p/10k
Piercing Navigator (Ivara) - 10.0p/10k
Duality (Equinox) - 8.0p/10k
Endless Lullaby (Baruuk) - 8.0p/10k
Resonance (Banshee) - 7.6p/10k
Resonating Quake (Banshee) - 7.6p/10k
Savage Silence (Banshee) - 7.6p/10k
Sonic Fracture (Banshee) - 7.6p/10k
---
Sorted by average:
Entropy Detonation (Obex) - 19.7p/10k
Ore Gaze (Atlas) - 16.1p/10k
Fireball Frenzy (Ember) - 15.7p/10k
Hushed Invisibility (Loki) - 15.3p/10k
Prey of Dynar (Voruna) - 15.3p/10k
Savior Decoy (Loki) - 15.2p/10k
Blood Forge (Garuda) - 15.1p/10k
Ironclad Flight (Titania) - 15.1p/10k
Path of Statues (Atlas) - 14.8p/10k
Empowered Quiver (Ivara) - 14.8p/10k
---
Sorted by average of bids within 1 stdev:
Toxic Sequence (Acrid) - 18.0p/10k
Piercing Navigator (Ivara) - 13.0p/10k
Empowered Quiver (Ivara) - 12.9p/10k
Entropy Spike (Bolto) - 12.6p/10k
Velocitus Barrel - 12.1p/10k
Ore Gaze (Atlas) - 12.1p/10k
Entropy Detonation (Obex) - 11.8p/10k
Scattered Justice (Hek) - 11.8p/10k
Savage Silence (Banshee) - 11.5p/10k
Healing Flame (Ember) - 11.5p/10k
```


# Personal discoveries
Much of this is conjecture, as I'm only one person and can only do so much trading (both due to in-game limits and my own patience), but it's very interesting to see the trends in the data, hence why I started this project at all. Due to its low volume, this market has been very hard to follow with my understanding of the data; I still have questions, but believe this has been a good starting point to find the answers I want.

When determining purchasing power as platinum per 10k standing, I confirmed that augment mods had the highest demand of anything from the faction shop and were often at or above the price range of anything that would reasonably compete with them in the market, with archwing parts being pretty similar due to being comparable in price and faction weapons being the least lucrative market in terms of pure standing to platinum efficiency; I was able to make profit in the past by day trading faction weapons on the market, but never in converting standing to platinum through faction weapons, as it was often easier to sell a few augment mods for that much platinum anyways. Due to the existence of some prime archwing weapons, as well as more modern archwing weapons, the faction archwing parts aren't quite as relevant, explaining the smaller market.

Without knowing the history of sales, which warframe.market can be unreliable in tracking due to the varied ways users can interact with its interface, or the SMA, which, as far as I can tell, is not exposed by the API itself, a scraping operation like this cannot account for what listings are actually taken; an item with a high purchasing power might not see many taken listings at all, whether an augment mod or another item. One augment mod I have frequent success trading on the market is Nezha's Divine Retribution, which I noted as having a relatively low purchasing power compared to other augment mods as it's often sold around or under 10p, while Hydroid's Viral Quills, a seemingly useful augment mod for a less popular warframe, had a high relative purchasing power but very low order volume on both the sells and buys during development, likely leading to the higher prices. (It seems the prices have evened out now, as it's being sold for around 10p like Divine Retribution, but I recall it being much higher up on the list at an earlier point in time.) I have been able to trade at least two copies of Divine Retribution every time I go online to trade, while none of the Viral Quills copies I've bought have sold yet. Another curious case is Partitioned Mallet, an Octavia augment mod: This warframe is considered quite good and this augment mod is easy to access in turn, with a large amount of listings, but the mod always seems to be priced higher than the average 10p, which would likely make it an interesting target to go after the next time I go trading.
