import re
from enum import Enum
from typing import List
from urllib.parse import urlparse

import requests

# Tournament pages are children of the site's "Campeonatos" page (id 14) in the CMS,
# regardless of category/year - confirmed against the live REST API (2026-08-23).
CAMPEONATOS_PARENT_PAGE_ID = 14
# 'campeonatos' itself shows up as its own child page (a self-referential content
# block, not a real tournament) - excluded rather than fed to the category filters.
NON_TOURNAMENT_SLUGS = {"campeonatos"}


def isFemaleTournament(url: str):
    return 'feminino' in url or 'feminina' in url or 'end-zone' in url

def isFlagTournament(url: str):
    return 'flag' in url or 'lineff' in url

def isMaleTournament(url: str):
    return not (isFlagTournament(url) or isFemaleTournament(url))


_TRAILING_YEAR_RE = re.compile(r'(\d{4})/?$')


def filter_urls_by_year(urls: List[str], since_year: int) -> List[str]:
    """Keeps only tournament URLs whose slug ends in a year >= since_year.

    URLs with no recognizable trailing year are kept rather than dropped, since
    silently losing an edge case is worse than scraping a URL we didn't strictly need.
    """
    filtered_urls = []

    for url in urls:
        match = _TRAILING_YEAR_RE.search(url)

        if match is None or int(match.group(1)) >= since_year:
            filtered_urls.append(url)

    return filtered_urls


class TournamentUrlsScrapper:
    class CompetitionCategory(Enum):
        FEMALE = "feminino"
        MALE = "masculino"
        FLAG = "flag"

    def __init__(self, base_url: str, category: str):
        parsed_base_url = urlparse(base_url)
        self.api_url = f"{parsed_base_url.scheme}://{parsed_base_url.netloc}/wp-json/wp/v2/pages"

        self.category = None
        self.category_function = None

        self.__parse_category(category)

    def get_urls(self) -> List[str]:
        pages = self.__fetch_tournament_pages()

        urls = [page['link'] for page in pages if page['slug'] not in NON_TOURNAMENT_SLUGS]
        urls = [url for url in urls if self.category_function(url)]

        return urls

    def __fetch_tournament_pages(self) -> List[dict]:
        # Replaces scraping the /campeonatos/ listing page's body content
        # (div.wpb_wrapper p a), which had silently stopped being updated after 2024 -
        # new tournaments since 2025, including the brand-new Superliga championship,
        # were missing from it entirely (confirmed 2026-08-23). Querying the CMS
        # parent/child relationship directly via the REST API has no such staleness: a
        # new tournament page shows up the moment it's published, with no year-guessing
        # or hardcoded link list needed. It also already returns clean, deduped,
        # correctly-spelled URLs - the DOM-scraping era's __append_missing_urls patches
        # (a typo'd matogrossense slug, a duplicated 2018 link, a missing 2019 one) were
        # verified unnecessary here and dropped rather than carried over.
        pages = []
        page_num = 1

        while True:
            response = requests.get(
                self.api_url,
                params={
                    "parent": CAMPEONATOS_PARENT_PAGE_ID,
                    "per_page": 100,
                    "page": page_num,
                    "_fields": "slug,link",
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()
            pages.extend(response.json())

            total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
            if page_num >= total_pages:
                break
            page_num += 1

        return pages

    def __parse_category(self, category: str):
        if category == "feminino":
            self.category = self.CompetitionCategory.FEMALE
            self.category_function = isFemaleTournament
        elif category == "masculino":
            self.category = self.CompetitionCategory.MALE
            self.category_function = isMaleTournament
        elif category == "flag":
            self.category = self.CompetitionCategory.FLAG
            self.category_function = isFlagTournament
        else:
            raise ValueError(f"Nome da categoria {category} inválido")

if __name__ == '__main__':
    url = 'https://www.salaooval.com.br/campeonatos/'

    tournaments_scrapper: TournamentUrlsScrapper = TournamentUrlsScrapper(url, 'masculino')

    urls = tournaments_scrapper.get_urls()

    print(urls)

    print(len(urls))

    for url in urls:
        print(url)
