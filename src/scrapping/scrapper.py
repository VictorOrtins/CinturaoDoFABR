from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from io import StringIO

import pandas as pd
import time



# Algumas ligas possuem tabelas que passam pra mais de uma página. Provavelmemte será necessário tratar isso. - 
# parece que ele tá carregando dinamicamente a segunda página. Então será necessário passar pra próximo e então pegar os dados


def get_table_df(table):
    html_da_tabela = table.get_attribute("outerHTML")
    df = pd.read_html(StringIO(html_da_tabela))[0]  # Extrai a tabela como DataFrame

    return df

def get_card_result(row):

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sp-event-date"))
    )

    date = row.find_element(By.CLASS_NAME, "sp-event-date").get_attribute('datetime')
    teams = row.find_elements(By.CSS_SELECTOR, "span.team-logo")
    mandante = teams[0].get_attribute("title")
    visitante = teams[1].get_attribute("title")
    resultado = row.find_element(By.CSS_SELECTOR, "h5.sp-event-results").text.replace("\n", " ")
    
    # Armazenar em um dicionário
    game_data = {
        "Data": date,
        "Mandante": mandante,
        "Hor/Res": resultado,
        "Visitante": visitante
    }

    return pd.DataFrame([game_data])


options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

all_games = pd.DataFrame()

url = 'http://www.salaooval.com.br/campeonatos/bfa-2023/#tabela'

driver.get(url)


WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.vc_tta-tabs-list li"))
)

tabs = driver.find_elements(By.CSS_SELECTOR, "ul.vc_tta-tabs-list li span.vc_tta-title-text")
print(len(tabs))

for tab in tabs:
    url = f'http://www.salaooval.com.br/campeonatos/bfa-2023/#{tab}'

    try:
        driver.get(url)
    except Exception:
        continue

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sp-event-list-format-homeaway"))
    )

    tables = driver.find_elements(By.CLASS_NAME, "sp-event-list-format-homeaway")
    for table in tables:
        df = get_table_df(table)
        all_games = pd.concat([all_games, df], ignore_index=True)


    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sp-event-blocks"))
    )

    WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "time.sp-event-date")))

    rows = driver.find_elements(By.CSS_SELECTOR, "table.sp-event-blocks.sp-data-table.sp-paginated-table tbody tr")

    df_cards = pd.DataFrame()
    for row in rows:
        df_cards = pd.concat([df_cards, get_card_result(row)], ignore_index=True)

    all_games = pd.concat([all_games, df_cards], ignore_index=True)

all_games = all_games.drop_duplicates(subset=["Data", "Mandante", "Hor/Res", "Visitante"])

print(len(all_games))

