from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import os
from urllib.parse import urlparse
import time

BASE_URL = "https://splatoon3.ink/data/archive/?prefix=2023/"
GECKO_DRIVER_PATH = "~/dev/SplatScratch/geckodriver"

from selenium.webdriver.support import expected_conditions as EC

def get_soup(url: str = BASE_URL) -> BeautifulSoup:
    print(f"Getting soup for {url}", end="\r")
    service = Service(GECKO_DRIVER_PATH)
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    # Wait for the page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "a"))
    )
    # Wait an additional quarter second for the page to finish loading
    time.sleep(0.25)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    return soup

def list_all_links(url: str = BASE_URL) -> list[str]:
    soup = get_soup(url)
    links = soup.find_all("a")
    return [link["href"] for link in links]

def get_last_directory() -> str:
    # Assume all directories but the last one are complete
    year_dirs = os.listdir("data/splatoon3_ink")
    year_dirs.sort()
    year_dir = year_dirs[-1]
    month_dirs = os.listdir(f"data/splatoon3_ink/{year_dir}")
    month_dirs.sort()
    month_dir = month_dirs[-1]
    day_dirs = os.listdir(f"data/splatoon3_ink/{year_dir}/{month_dir}")
    day_dirs.sort()
    day_dir = day_dirs[-1]

    return f"data/splatoon3_ink/{year_dir}/{month_dir}/{day_dir}"

def get_date_from_link(link: str) -> tuple[int, ...]:
    base_url = "https://splatoon3.ink/data/archive/?prefix="
    # Remove the base url if it exists
    if link.startswith(base_url):
        link = link[len(base_url):]
    # Remove the trailing slash if it exists
    if link.endswith("/"):
        link = link[:-1]
    dates = link.split("/")
    dates.append("99") # Add a dummy value to ensure (2023, 1) >= (2023, 1, 1)
    # Not all links will have the same number of subdirectories
    pre_out = [int(x) for x in dates]
    return tuple(pre_out[:3])

def list_all_links_recursive(url: str = BASE_URL, last_date: tuple[int, int, int] | None = None) -> list[str]:
    """Gets all links from the given url and all subdirectories. Only returns links to json files.

    Assumes the last directory in the data directory is incomplete and will return all links from that directory.

    Args:
        url (str, optional): URL to start from. Defaults to BASE_URL.
        last_date (tuple[int, int, int] | None): The last date to return links for. Defaults to None.

    Returns:
        list[str]: List of links to json files.
    """
    if last_date is None:
        last_date = get_last_directory().split("/")[-3:]
        last_date = tuple(int(x) for x in last_date)
    
    links = list_all_links(url)
    json_links = [link for link in links if link.endswith(".json")]
    non_json_links = [link for link in links if not link.endswith(".json")]
    # Remove broken links
    non_json_links = [link for link in non_json_links if link.startswith(BASE_URL)]
    # Remove links that are too old
    non_json_links = [link for link in non_json_links if get_date_from_link(link) >= last_date]

    for link in non_json_links:
        json_links.extend(list_all_links_recursive(link))
    return json_links

if __name__ == "__main__":
    links = list_all_links_recursive()
    with open("all_links.txt", "w") as f:
        f.write("\n".join(links))
