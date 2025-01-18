import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.scrapping.scrapper import GamesScrapper

class TestGamesScrapper:
    def test_bfa_2024(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/bfa-2024/'])

        bfa_2024_df = scrapper.scrape_tournaments()

        assert len(bfa_2024_df) == 52
        assert len(bfa_2024_df[~bfa_2024_df['Campo'].isna()]) == 35 # 38 jogos da regular teriam essa coluna, porém 3 não tem campo cadastrados


        coyotes_arsenal = bfa_2024_df[(bfa_2024_df['Mandante'] == 'Sinop Coyotes') & (bfa_2024_df['Visitante'] == 'Cuiabá Arsenal')]
        assert len(coyotes_arsenal) == 1

        assert coyotes_arsenal['Hor/Res'].iloc[0] == '18 - 13'
        assert coyotes_arsenal['Data'].iloc[0] == '2024-06-29 17:00:00'


        rex_mariners = bfa_2024_df[(bfa_2024_df['Mandante'] == 'Timbó Rex') & (bfa_2024_df['Visitante'] == 'Recife Mariners')]
        assert len(rex_mariners) == 1

        assert rex_mariners['Hor/Res'].iloc[0] == '14 - 26'
        assert rex_mariners['Data'].iloc[0] == '2024-11-02 16:00:09'


        rex_galo = bfa_2024_df[(bfa_2024_df['Mandante'] == 'Recife Mariners') & (bfa_2024_df['Visitante'] == 'Galo FA')]
        assert len(rex_galo) == 1

        assert rex_galo['Hor/Res'].iloc[0] == '22 - 06'
        assert rex_galo['Data'].iloc[0] == '2024-12-01 15:00:49'

    def test_campeonato_brasileiro_2012(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/campeonato-brasileiro-2012/'])

        brasileiro_2012 = scrapper.scrape_tournaments()

        assert len(brasileiro_2012) == 108
        assert len(brasileiro_2012[~brasileiro_2012['Campo'].isna()]) == 108 - 16 # 38 jogos da regular teriam essa coluna, porém 3 não tem campo cadastrados


        espectros_mariners = brasileiro_2012[(brasileiro_2012['Mandante'] == 'João Pessoa Espectros') & (brasileiro_2012['Visitante'] == 'Recife Mariners')]
        assert len(espectros_mariners) == 1

        assert espectros_mariners['Hor/Res'].iloc[0] == '43 - 06'
        assert espectros_mariners['Data'].iloc[0] == '2012-07-01 14:00:00'


        spartans_brasil = brasileiro_2012[(brasileiro_2012['Mandante'] == 'Spartans Football') & (brasileiro_2012['Visitante'] == 'Brasil Devilz')]
        assert len(spartans_brasil) == 1

        assert spartans_brasil['Hor/Res'].iloc[0] == '03 - 06'
        assert spartans_brasil['Data'].iloc[0] == '2012-07-15 14:00:00'

        pumpkins_chacais = brasileiro_2012[(brasileiro_2012['Mandante'] == 'Porto Alegre Pumpkins') & (brasileiro_2012['Visitante'] == 'Santa Cruz Chacais')]
        assert len(pumpkins_chacais) == 1

        assert pumpkins_chacais['Hor/Res'].iloc[0] == '26 - 08'
        assert pumpkins_chacais['Data'].iloc[0] == '2012-09-30 14:00:00'

        bulls_bravos = brasileiro_2012[(brasileiro_2012['Mandante'] == 'Bulls Potiguares') & (brasileiro_2012['Visitante'] == 'Sergipe Bravos')]
        assert len(bulls_bravos) == 1

        assert bulls_bravos['Hor/Res'].iloc[0] == '50 - 09'
        assert bulls_bravos['Data'].iloc[0] == '2012-10-13 14:00:00'

        cuiaba_pumpkins = brasileiro_2012[(brasileiro_2012['Mandante'] == 'Cuiabá Arsenal') & (brasileiro_2012['Visitante'] == 'Porto Alegre Pumpkins')]
        assert len(cuiaba_pumpkins) == 1

        assert cuiaba_pumpkins['Hor/Res'].iloc[0] == '41 - 07'
        assert cuiaba_pumpkins['Data'].iloc[0] == '2012-10-27 14:00:00'


        cuiaba_crocodiles = brasileiro_2012[(brasileiro_2012['Mandante'] == 'Cuiabá Arsenal') & (brasileiro_2012['Visitante'] == 'Coritiba Crocodiles')]
        assert len(cuiaba_crocodiles) == 1

        assert cuiaba_crocodiles['Hor/Res'].iloc[0] == '31 - 23'
        assert cuiaba_crocodiles['Data'].iloc[0] == '2012-11-24 14:00:00'

    def test_spfl_2018(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/sao-paulo-football-league-2018/'])

        spfl_2012 = scrapper.scrape_tournaments()

        assert len(spfl_2012) == 47
        assert len(spfl_2012[~spfl_2012['Campo'].isna()]) == 42


        piracicaba_mooca = spfl_2012[(spfl_2012['Mandante'] == 'Piracicaba Cane Cutters') & (spfl_2012['Visitante'] == 'Mooca Destroyers')]
        assert len(piracicaba_mooca) == 1

        assert piracicaba_mooca['Hor/Res'].iloc[0] == '36 - 20'
        assert piracicaba_mooca['Data'].iloc[0] == '2018-03-18 14:00:00'


        storm_lizards = spfl_2012[(spfl_2012['Mandante'] == 'São Paulo Storm') & (spfl_2012['Visitante'] == 'Empyreo Leme Lizards')]
        assert len(storm_lizards) == 1

        assert storm_lizards['Hor/Res'].iloc[0] == '37 - 00'
        assert storm_lizards['Data'].iloc[0] == '2018-06-10 14:00:00'


        rhynos_storm = spfl_2012[(spfl_2012['Mandante'] == 'Guarulhos Rhynos') & (spfl_2012['Visitante'] == 'São Paulo Storm')]
        assert len(rhynos_storm) == 2

        assert rhynos_storm['Hor/Res'].iloc[0] == '48 - 20'
        assert rhynos_storm['Data'].iloc[0] == '2018-03-10 10:00:00'

        assert rhynos_storm['Hor/Res'].iloc[1] == '21 - 18'
        assert rhynos_storm['Data'].iloc[1] == '2018-07-08 10:00:09'

    def test_nordeste_2019(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/copa-nordeste-2019/'])

        nordeste_2019 = scrapper.scrape_tournaments()

        assert len(nordeste_2019) == 5

        bulls_patos = nordeste_2019[(nordeste_2019['Mandante'] == 'Bulls Potiguares 2') & (nordeste_2019['Visitante'] == 'Patos FA')]
        assert len(bulls_patos) == 1

        assert bulls_patos['Hor/Res'].iloc[0] == '31 - 23'
        assert bulls_patos['Data'].iloc[0] == '2019-04-28 15:00:00'


        redbulls_bulls = nordeste_2019[(nordeste_2019['Mandante'] == 'Santana Red Bulls') & (nordeste_2019['Visitante'] == 'Bulls Potiguares 2')]
        assert len(redbulls_bulls) == 1

        assert redbulls_bulls['Hor/Res'].iloc[0] == '25 - 14'
        assert redbulls_bulls['Data'].iloc[0] == '2019-08-10 18:00:00'

    def test_two_leagues(self):
        urls_list = ['http://www.salaooval.com.br/campeonatos/bfa-2024/', 'http://www.salaooval.com.br/campeonatos/campeonato-brasileiro-2012/']

        scrapper = GamesScrapper(urls_list)

        all_games = scrapper.scrape_tournaments()

        assert len(all_games) == 160





