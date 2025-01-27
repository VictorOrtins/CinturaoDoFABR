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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.utils.utils import get_dominant_color

class TeamsScrapper:
    def __init__(self, urls_to_scrape: List[str], save_path: str, wait_time=30):
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

    def scrape_teams(self, init, end, verbose=False) -> pd.DataFrame:
        all_teams = pd.DataFrame()

        urls_to_scrape = self.urls_to_scrape[init:end]

        for index, url in enumerate(urls_to_scrape):
            time = url.split('/')[-2]

            if verbose:
                print(f"--- {index + init} => {time} está sendo vasculhado ---")

            try:
                self.driver.get(url)
            except Exception:
                continue

            current_url  = self.driver.current_url
            
            try:
                team_info = self.__scrape_team(current_url)
            except Exception as e:
                if verbose:
                    print(e)
                
                continue

            all_teams = pd.concat([all_teams, pd.DataFrame([team_info])], ignore_index=True)

            self.__save_to_csv(all_teams)

        all_teams = all_teams.drop_duplicates(subset=['Nome'])

        return all_teams

    
    def __scrape_team(self, url: str) -> dict:
        url = url + '/' if not url.endswith('/') else url
        team_prefix = url.split('/')[-3]

        try:
            if team_prefix == 'times':
                return self.__scrape_complete_team_info(url)
            elif team_prefix == 'team' or team_prefix == 'equipe':
                return self.__scrape_short_team_info(url)
            else:
                raise Exception(f"Um dos times não segue o padrão - {url}")
        except Exception as e:
            raise e
            
        
    def __scrape_complete_team_info(self, url) -> dict:
        try:
            team_name = self.driver.find_elements(By.CSS_SELECTOR, "div.wpb_wrapper h1")

        
            team_name = ' '.join([word.get_attribute('textContent').strip() for word in team_name])

            img_url = self.driver.find_element(By.CSS_SELECTOR, "figure.wpb_wrapper a.vc_single_image-wrapper").get_attribute("href")
            team_sede = self.driver.find_element(By.XPATH, "//p[contains(., 'Sede')]").get_attribute('textContent').split("Sede")[-1].strip().split("\n")[0]

            team_color = get_dominant_color(img_url)
        except Exception:
            raise ValueError("Time não encontrado - Error 404")
    
        return {
            "Nome": team_name,
            "URL da Imagem": img_url,
            "Sede": team_sede,
            "Cor Primária": team_color,
            "URL": url,
        }

    def __scrape_short_team_info(self, url) -> dict:
        try:
            team_name = self.driver.find_element(By.CSS_SELECTOR, "div.td-page-header h1.entry-title span").get_attribute('textContent')


            img_url = self.driver.find_element(By.CSS_SELECTOR, "div.sp-template-team-logo img").get_attribute('src')
            img_url = img_url.replace('-128x128', '')
            
            team_color = get_dominant_color(img_url)
        except Exception:
            raise ValueError("Nome do time não encontrado - Error 404")

        return {
            "Nome": team_name,
            "URL da Imagem": img_url,
            "Sede": None,
            "Cor Primária": team_color,
            "URL": url
        }
    
    def __save_to_csv(self, dataframe: pd.DataFrame):
        if self.save_path is None:
            return
        

        dataframe.to_csv(self.save_path, index=False, header=True)

if __name__ == '__main__':
    urls = ['http://www.salaooval.com.br/times/galo-fa/', 'http://www.salaooval.com.br/times/joao-pessoa-espectros/', 'http://www.salaooval.com.br/equipe/cruzeiro-guardians/']

    scrapper = TeamsScrapper(urls, save_path='team.csv')

    teams_df = scrapper.scrape_teams(0, 3, verbose=True)

    print(teams_df.head())