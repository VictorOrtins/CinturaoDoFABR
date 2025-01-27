from get_urls import TeamUrlsScrapper
from scrapper import TeamsScrapper


if __name__ == '__main__':
    urls_scrapper = TeamUrlsScrapper(base_url='https://www.salaooval.com.br/times/')
    urls = urls_scrapper.get_urls()
    
    games_scrapper = TeamsScrapper(urls, save_path='data/teams.csv')
    all_games = games_scrapper.scrape_teams(init=0, end=len(urls), verbose=True)