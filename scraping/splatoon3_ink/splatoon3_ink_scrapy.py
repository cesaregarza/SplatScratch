import json
import os
from urllib.parse import urlparse

import scrapy


def get_filename_path(url: str) -> tuple[str, str]:
    filename = os.path.basename(urlparse(url).path)
    year, month, day = filename.split(".")[0].split("-")
    directory = f"data/splatoon3_ink/{year}/{month}/{day}"
    if "xrank" in filename:
        directory += "/xrank"
    path = f"{directory}/{filename}"
    return path, directory


class JsonDownloadSpider(scrapy.Spider):
    name = "jsondownload"

    def start_requests(self):
        with open("all_links.txt", "r") as f:
            for link in f.read().splitlines():
                path, _ = get_filename_path(link)
                # Only download the file if it doesn't already exist
                if os.path.exists(path):
                    continue
                yield scrapy.Request(url=link, callback=self.parse)

    def parse(self, response):
        link = response.url
        path, directory = get_filename_path(link)
        if not os.path.exists(path):
            if not os.path.exists(directory):
                os.makedirs(directory)
            data = json.loads(response.text)
            with open(path, "w") as f:
                json.dump(data, f)
