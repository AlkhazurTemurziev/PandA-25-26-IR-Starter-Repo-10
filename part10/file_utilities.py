# file_utilities.py - same as part 9

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any

from .constants import POETRYDB_URL, CACHE_FILENAME


class Configuration:
    def __init__(self):
        self.highlight = True
        self.search_mode = "AND"
        self.hl_mode = "DEFAULT"

    def copy(self):
        copy = Configuration()
        copy.highlight = self.highlight
        copy.search_mode = self.search_mode
        copy.hl_mode = self.hl_mode
        return copy

    def update(self, other: Dict[str, Any]):
        if "highlight" in other and isinstance(other["highlight"], bool):
            self.highlight = other["highlight"]

        if "search_mode" in other and other["search_mode"] in ["AND", "OR"]:
            self.search_mode = other["search_mode"]

        if "hl_mode" in other and other["hl_mode"] in ["DEFAULT", "GREEN"]:
            self.hl_mode = other["hl_mode"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highlight": self.highlight,
            "search_mode": self.search_mode,
            "hl_mode": self.hl_mode,
        }

    def save(self):
        config_file_path = module_relative_path("config.json")
        try:
            with open(config_file_path, "w") as config_file:
                json.dump(self.to_dict(), config_file, indent=4)
        except OSError:
            print(f"Writing config.json failed.")


def module_relative_path(name: str) -> str:
    return os.path.join(os.path.dirname(__file__), name)


DEFAULT_CONFIG = Configuration()


def load_config() -> Configuration:
    config_file_path = module_relative_path("config.json")

    cfg = DEFAULT_CONFIG.copy()
    try:
        with open(config_file_path) as config_file:
            cfg.update(json.load(config_file))
    except FileNotFoundError:
        print("No config.json found. Using default configuration.")
        return cfg
    except json.JSONDecodeError:
        print("config.json is invalid. Using default configuration.")
        return cfg
    except OSError:
        print("Could not read config.json. Using default configuration.")
        return cfg

    return cfg


def fetch_sonnets_from_api():
    from .models import Sonnet

    sonnets = []
    try:
        with urllib.request.urlopen(POETRYDB_URL, timeout=10) as response:
            data = response.read()
            raw_sonnets = json.loads(data)
    except Exception as e:
        print("Error fetching from API:", e)
        return []

    for s in raw_sonnets:
        sonnets.append(Sonnet(s))
    return sonnets


def load_sonnets():
    from .models import Sonnet

    cache_file = module_relative_path(CACHE_FILENAME)

    if os.path.exists(cache_file):
        print("Loaded sonnets from the cache.")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        sonnets = []
        for s in raw_data:
            sonnets.append(Sonnet(s))
        return sonnets

    print("Downloading sonnets from PoetryDB...")
    sonnets = fetch_sonnets_from_api()

    raw_data = []
    for s in sonnets:
        raw_data.append({"title": s.title, "lines": s.lines})

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    return sonnets