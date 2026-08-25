from src.scrapping.scrape_games.get_urls import TournamentUrlsScrapper, filter_urls_by_year


class TestFilterUrlsByYear:
    def test_keeps_urls_at_or_after_since_year(self):
        urls = [
            "http://www.salaooval.com.br/campeonatos/bfa-2024/",
            "http://www.salaooval.com.br/campeonatos/bfa-2023/",
        ]

        filtered = filter_urls_by_year(urls, since_year=2023)

        assert filtered == urls

    def test_drops_urls_before_since_year(self):
        urls = [
            "http://www.salaooval.com.br/campeonatos/bfa-2024/",
            "http://www.salaooval.com.br/campeonatos/campeonato-mato-grossense-2015/",
        ]

        filtered = filter_urls_by_year(urls, since_year=2020)

        assert filtered == ["http://www.salaooval.com.br/campeonatos/bfa-2024/"]

    def test_boundary_year_is_kept(self):
        urls = ["http://www.salaooval.com.br/campeonatos/bfa-2023/"]

        filtered = filter_urls_by_year(urls, since_year=2023)

        assert filtered == urls

    def test_url_without_trailing_year_is_kept_rather_than_dropped(self):
        urls = ["http://www.salaooval.com.br/campeonatos/taca-nove-de-julho/"]

        filtered = filter_urls_by_year(urls, since_year=2023)

        assert filtered == urls

    def test_url_without_trailing_slash_still_matches(self):
        urls = ["http://www.salaooval.com.br/campeonatos/bfa-2024"]

        filtered = filter_urls_by_year(urls, since_year=2024)

        assert filtered == urls


class TestTournamentUrlsScrapper:
    # URL discovery used to scrape the /campeonatos/ listing page's body content
    # (div.wpb_wrapper p a), which silently stopped getting new tournaments added to it
    # after 2024 - anything from 2025 on, including the brand-new Superliga national
    # championship, was invisible to the scraper even though the pages existed and had
    # real game data. Switched to querying the site's WordPress REST API directly
    # (every tournament page is a child of the same CMS parent page, id 14), which has
    # no such staleness. This test exists so a future regression back to DOM-scraping
    # the listing page doesn't silently reintroduce the same blind spot (found
    # 2026-08-23 while running the Phase 1 bootstrap scrape).
    def test_finds_recent_and_new_tournaments_missing_from_the_listing_page(self):
        scrapper = TournamentUrlsScrapper(base_url="http://www.salaooval.com.br/campeonatos/", category="masculino")

        urls = scrapper.get_urls()

        assert "https://www.salaooval.com.br/campeonatos/superliga-2025/" in urls
        assert "https://www.salaooval.com.br/campeonatos/superliga-2026/" in urls
        assert "https://www.salaooval.com.br/campeonatos/campeonato-pernambucano-2025/" in urls

    def test_excludes_the_self_referential_campeonatos_page(self):
        scrapper = TournamentUrlsScrapper(base_url="http://www.salaooval.com.br/campeonatos/", category="masculino")

        urls = scrapper.get_urls()

        assert not any(url.rstrip("/").endswith("/campeonatos/campeonatos") for url in urls)

    def test_categories_are_mutually_exclusive_between_male_and_flag(self):
        male_urls = TournamentUrlsScrapper(
            base_url="http://www.salaooval.com.br/campeonatos/", category="masculino"
        ).get_urls()
        flag_urls = TournamentUrlsScrapper(
            base_url="http://www.salaooval.com.br/campeonatos/", category="flag"
        ).get_urls()

        assert set(male_urls).isdisjoint(flag_urls)
