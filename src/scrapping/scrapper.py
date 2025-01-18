from io import StringIO
import os
import sys
from typing import List

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.utils.utils import is_datetime


class GamesScrapper:
    def __init__(self, urls_to_scrape: List[str], save_path, wait_time=30):
        self.urls_to_scrape = urls_to_scrape
        self.wait_time = wait_time
        self.save_path = save_path

        self.driver = None
        self.__init_driver()

    def __init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        self.driver = driver

    def scrape_tournaments(self, init, end, verbose=False) -> pd.DataFrame:
        all_games = pd.DataFrame()

        urls_to_scrape = self.urls_to_scrape[init:end]

        for index, url in enumerate(urls_to_scrape):

            tournament = url.split('/')[-2]

            if verbose:
                print(f"--- {index + init} => {tournament} está sendo vasculhado --- ")
            
            self.driver.get(url)

            tournament_tabs = self.__find_tournament_tabs()

            if tournament_tabs is None:
                print("Foram encontrados 0 jogos na URL")
                continue

            all_games_url = self.__scrape_tournament(tournament_tabs, url)

            all_games = pd.concat([all_games, all_games_url], ignore_index=True)

            if len(all_games) != 0:
                all_games['Data'] = all_games['Data'].apply(self.__format_date)
                all_games['Torneio'] = tournament

            if verbose:
                qtd_games = len(all_games_url)
                print(f"Foram encontrados {qtd_games} jogos na URL")
                print(f"Registros sendo salvos no path {self.save_path}")
            
            self.__save_to_csv(all_games)

        return all_games


    def __find_tournament_tabs(self) -> List[WebElement]:
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.vc_tta-tabs-list li"))
            )
        except Exception:
            return None

        tabs = self.driver.find_elements(By.CSS_SELECTOR, "ul.vc_tta-tabs-list li span.vc_tta-title-text")

        return tabs
    
    def __get_tab_url(self, url: str) -> bool:
        try:
            self.driver.get(url)
        except Exception:
            return False
        
        return True
    
    def __button_clicked(self, button: bool) -> bool:
        try:
            button.click()
        except Exception:
            return False
        
        return True
    
    def __find_elements(self, by: By, pattern: str) -> List[WebElement]:
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((by, pattern))
            )
        except Exception:
            return None
        
        elements = self.driver.find_elements(by, pattern)

        return elements

    def __scrape_tournament(self, tournament_tabs: List[WebElement], url: str) -> pd.DataFrame:
        all_games_url = pd.DataFrame()

        tournament_tabs_text = [tab.get_attribute('textContent') for tab in tournament_tabs]
        
        for tab_text in tournament_tabs_text:
            scrape_url = f'{url}#{tab_text.lower()}'
        
            if not self.__get_tab_url(scrape_url):
                continue

            buttons = self.__find_elements(By.CSS_SELECTOR, ".paginate_button")

            if buttons is not None:
                for button in buttons:
                    
                    if not self.__button_clicked(button):
                        continue
                    
                    all_games_url = self.__scrape_games(all_games_url)
            else:
                all_games_url = self.__scrape_games(all_games_url)

            all_games_url = all_games_url.drop_duplicates(subset=["Data", "Mandante", "Hor/Res", "Visitante"])
            
        return all_games_url

    def __scrape_homeaway_table(self) -> pd.DataFrame:
        all_games_homeaway = pd.DataFrame()
        tables = self.__find_elements(By.CLASS_NAME, "sp-event-list-format-homeaway")

        if tables is None:
            return all_games_homeaway
        
        for table in tables:
            df = self.__get_table_df(table)
            all_games_homeaway = pd.concat([all_games_homeaway, df], ignore_index=True)

        return all_games_homeaway

    def __scrape_cards(self) -> pd.DataFrame:
        all_games_cards = pd.DataFrame()

        WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "time.sp-event-date")))

        rows = self.__find_elements(By.CSS_SELECTOR, "table.sp-event-blocks.sp-data-table.sp-paginated-table tbody tr")

        if rows is None:
            return all_games_cards


        df_cards = pd.DataFrame()
        for row in rows:
            df_cards = pd.concat([df_cards, self.__get_card_result(row)], ignore_index=True)
            all_games_cards = pd.concat([all_games_cards, df_cards], ignore_index=True)

        return all_games_cards

    def __get_card_result(self, row: WebElement) -> pd.DataFrame:
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sp-event-date"))
        )

        date = row.find_element(By.CLASS_NAME, "sp-event-date").get_attribute('datetime')
        teams = row.find_elements(By.CSS_SELECTOR, "span.team-logo")
        mandante = teams[0].get_attribute("title")
        visitante = teams[1].get_attribute("title")

        WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h5.sp-event-results span.sp-result")))

        try:
            pontos_mandante = row.find_element(By.CSS_SELECTOR, "h5.sp-event-results span.sp-result.ok").get_attribute('textContent')
            pontos_visitante = row.find_element(By.CSS_SELECTOR, "h5.sp-event-results span.sp-result:not(.ok)").get_attribute('textContent')
        except Exception:
            pontos = row.find_elements(By.CSS_SELECTOR, "h5.sp-event-results span.sp-result")
            try:
                pontos_mandante = pontos[0].get_attribute('textContent')
                pontos_visitante = pontos[1].get_attribute('textContent')
            except Exception:
                pontos_mandante = 'X'
                pontos_visitante = 'X'

        # Armazenar em um dicionário
        game_data = {
            "Data": date,
            "Mandante": mandante,
            "Hor/Res": f"{pontos_mandante} - {pontos_visitante}",
            "Visitante": visitante
        }

        return pd.DataFrame([game_data])

    def __get_table_df(self, table: WebElement) -> pd.DataFrame:
        html_da_tabela = table.get_attribute("outerHTML")
        df = pd.read_html(StringIO(html_da_tabela))[0]  # Extrai a tabela como DataFrame

        return df
    
    def __scrape_games(self, all_games_url: pd.DataFrame):        
        all_games_url = pd.concat([all_games_url, self.__scrape_homeaway_table()], ignore_index=True)
        all_games_url = pd.concat([all_games_url, self.__scrape_cards()], ignore_index=True)

        return all_games_url
    
    def __format_date(self, date):
        if isinstance(date, float): ##Faço a menor ideia do que fazer aqui KKKKK
            return date
        
        is_date_datetime = is_datetime(date)
        if is_date_datetime:
            return date
        else:
            if isinstance(date, str):
                return date[:19]
    
    def __save_to_csv(self, all_games: pd.DataFrame):
        if self.save_path is None:
            return
        

        all_games.to_csv(self.save_path, index=False, header=True)
        


    
if __name__ == '__main__':
    scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/bfa-2024/'])

    all_games = scrapper.scrape_tournaments()

    print(len(all_games))

    print(all_games.head())

    print(all_games.tail())


