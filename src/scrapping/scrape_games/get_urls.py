from enum import Enum
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement



def isFemaleTournament(url: str):
    return 'feminino' in url or 'feminina' in url or 'end-zone' in url

def isFlagTournament(url: str):
    return 'flag' in url or 'lineff' in url

def isMaleTournament(url: str):
    return not (isFlagTournament(url) or isFemaleTournament(url))


class TournamentUrlsScrapper:
    class CompetitionCategory(Enum):
        FEMALE = "feminino"
        MALE = "masculino"
        FLAG = "flag"


    def __init__(self, base_url: str, category: str):
        self.base_url = base_url

        self.driver = None
        self.__init_driver()

        self.category = None
        self.category_function = None

        self.__parse_category(category)



    def get_urls(self) -> List[str]:
        self.driver.get(self.base_url)

        links = self.__locate_possible_links()

        urls = self.__filter_urls(links)

        urls = self.__fix_urls(urls)

        urls = self.__append_missing_urls(urls)

        return urls

    def __init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        self.driver = driver

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

    def __locate_possible_links(self) -> List[WebElement]:
        css_tournament_selector = "div.wpb_wrapper p a"

        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_tournament_selector))
        )

        links = self.driver.find_elements(By.CSS_SELECTOR, css_tournament_selector)

        return links
    
    def __filter_urls(self, links) -> List[str]:
        urls = [link.get_attribute('href') for link in links]
        urls = [url for url in urls if self.category_function(url)]

        return urls
    

    def __append_missing_urls(self, urls: List[str]) -> List[str]:
        urls.append('https://www.salaooval.com.br/campeonatos/taca-nove-de-julho-2023/')

        try:
            urls.remove('http://www.salaooval.com.br/campeonatos/campeonato-matogrossense-2015/')
            urls.append('https://www.salaooval.com.br/campeonatos/campeonato-mato-grossense-2015/')
        except Exception:
            pass

        try:
            first_matogrossense_2018 = urls.index('http://www.salaooval.com.br/campeonatos/campeonato-mato-grossense-2018/')
            try:
                second_matogrossense_2018 = urls[first_matogrossense_2018 + 1:].index('http://www.salaooval.com.br/campeonatos/campeonato-mato-grossense-2018/') + first_matogrossense_2018 + 1                
                del urls[second_matogrossense_2018]
                urls.append('http://www.salaooval.com.br/campeonatos/campeonato-mato-grossense-2019/')
            except ValueError:
                pass
        except ValueError:
            pass

        return urls
    
    def __fix_urls(self, urls: List[str]) -> List[str]:
        urls = [url if url.endswith('/') else url + '/' for url in urls]
        return urls
    
if __name__ == '__main__':
    url = 'https://www.salaooval.com.br/campeonatos/#nacionais'

    tournaments_scrapper: TournamentUrlsScrapper = TournamentUrlsScrapper(url, 'masculino')

    urls = tournaments_scrapper.get_urls()

    print(urls)

    print(len(urls))

    for url in urls:
        print(url)

