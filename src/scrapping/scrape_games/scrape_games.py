from src.scrapping.scrape_games.get_urls import TournamentUrlsScrapper
from src.scrapping.scrape_games.scrapper import GamesScrapper


if __name__ == '__main__':
    urls_scrapper = TournamentUrlsScrapper(base_url='http://www.salaooval.com.br/campeonatos/', category='masculino')
    urls = urls_scrapper.get_urls()
    
    games_scrapper = GamesScrapper(urls, save_path='data/games.csv')
    all_games = games_scrapper.scrape_tournaments(init=0, end=len(urls), verbose=True)
