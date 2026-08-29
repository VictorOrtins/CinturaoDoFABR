from typing import List

import requests


class TeamUrlsScrapper:
    def __init__(self, base_url: str):
        self.api_url = self.__build_api_url(base_url)

    def get_urls(self) -> List[str]:
        teams = self.__fetch_teams()

        urls = [team['link'] for team in teams]

        return urls

    def __build_api_url(self, base_url: str) -> str:
        from urllib.parse import urlparse

        parsed_base_url = urlparse(base_url)
        return f"{parsed_base_url.scheme}://{parsed_base_url.netloc}/wp-json/sportspress/v2/teams"

    def __fetch_teams(self) -> List[dict]:
        # Replaces scraping the /times/ listing page's rendered links
        # (div.wpb_wrapper p a), which - like the equivalent tournament-listing page -
        # doesn't reliably surface every team (confirmed 2026-08-25: brand-new 2026
        # teams like Calvary Cavaliers/Ponta Grossa Phantoms were missing from it).
        # Teams are a SportsPress custom post type (sp_team) with its own REST
        # namespace (sportspress/v2, not wp/v2) - querying it directly returns every
        # published team (429, vs. 358 via the old DOM scrape) with no staleness and
        # no hardcoded missing-URL patch list needed. Use each team's own 'link' field
        # rather than its 'slug' - the two can differ (e.g. slug 'tigres-fa' with link
        # .../times/tigres-futebol-americano/), and 'link' is the actual scrapable URL.
        teams = []
        page_num = 1

        while True:
            response = requests.get(
                self.api_url,
                params={
                    "per_page": 100,
                    "page": page_num,
                    "_fields": "link",
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()
            teams.extend(response.json())

            total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
            if page_num >= total_pages:
                break
            page_num += 1

        return teams


if __name__ == '__main__':
    url = 'https://www.salaooval.com.br/times/'

    teams_scrapper: TeamUrlsScrapper = TeamUrlsScrapper(url)

    urls = teams_scrapper.get_urls()

    print(urls)

    print(len(urls))

    for url in urls:
        print(url)
