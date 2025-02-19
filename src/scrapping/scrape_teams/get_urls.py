from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement

class TeamUrlsScrapper:
    def __init__(self, base_url: str):
        self.base_url = base_url

        self.driver = None
        self.__init_driver()



    def get_urls(self) -> List[str]:
        self.driver.get(self.base_url)

        links = self.__locate_possible_links()

        urls = self.__filter_urls(links)

        urls = self.__fix_urls(urls)

        urls = self.__add_missing_urls(urls)

        return urls

    def __init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        self.driver = driver

    def __locate_possible_links(self) -> List[WebElement]:
        css_tournament_selector = "div.wpb_wrapper p a"

        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_tournament_selector))
        )

        links = self.driver.find_elements(By.CSS_SELECTOR, css_tournament_selector)

        return links
    
    def __filter_urls(self, links) -> List[str]:
        urls = [link.get_attribute('href') for link in links]

        return urls
    
    def __fix_urls(self, urls: List[str]) -> List[str]:
        urls = [url if url.endswith('/') else url + '/' for url in urls]
        return urls
    
    def __add_missing_urls(self, urls: List[str]) -> List[str]:
        urls.append('http://www.salaooval.com.br/equipe/almirantes-fa/')
        urls.append('https://www.salaooval.com.br/times/istepos-fa/')
        urls.append('http://www.salaooval.com.br/times/manaus-fa/')
        urls.append('http://www.salaooval.com.br/equipe/brusque-admirals/')
        urls.append('https://www.salaooval.com.br/equipe/blumenau-riesen/')
        urls.append('https://www.salaooval.com.br/times/spartans-football/')
        urls.append('http://www.salaooval.com.br/equipe/cabritos-fa/')
        urls.append('https://www.salaooval.com.br/equipe/brasil-devilz/')
        urls.append('https://www.salaooval.com.br/times/guardian-saints/')
        urls.append('https://www.salaooval.com.br/equipe/unicentro-knights/')
        urls.append('https://www.salaooval.com.br/times/black-hawks/')
        urls.append('https://www.salaooval.com.br/times/tritoes-fa/')
        urls.append('https://www.salaooval.com.br/times/tigres-futebol-americano/')
        urls.append('https://www.salaooval.com.br/times/blaze-fa/')

        return urls
    
if __name__ == '__main__':
    url = 'https://www.salaooval.com.br/times/'

    tournaments_scrapper: TeamUrlsScrapper = TeamUrlsScrapper(url)

    urls = tournaments_scrapper.get_urls()

    print(urls)

    print(len(urls))

    for url in urls:
        print(url)


