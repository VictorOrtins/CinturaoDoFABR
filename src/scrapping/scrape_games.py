from get_urls import TournamentUrlsScrapper
from scrapper import GamesScrapper


if __name__ == '__main__':
    urls_scrapper = TournamentUrlsScrapper(base_url='http://www.salaooval.com.br/campeonatos/', category='masculino')
    urls = urls_scrapper.get_urls()
    
    games_scrapper = GamesScrapper(urls, save_path='games5.csv')
    # Já tá no número certo!!! Lembra de apagar essa msg qnd executar dnv
    all_games = games_scrapper.scrape_tournaments(init=47, end=len(urls), verbose=True)

    all_games.to_csv('games6.csv')