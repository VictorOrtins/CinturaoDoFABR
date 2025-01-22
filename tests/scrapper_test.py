import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.scrapping.scrapper import GamesScrapper

class TestGamesScrapper:
    #Nacional 1
    def test_bfa_2024(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/bfa-2024/'], save_path=None)

        bfa_2024_df = scrapper.scrape_tournaments(init=0, end=1)

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
    
    # Nacional 2 - Com jogos páginados
    def test_campeonato_brasileiro_2012(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/campeonato-brasileiro-2012/'], save_path=None)

        brasileiro_2012 = scrapper.scrape_tournaments(init=0, end=1)

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
    
    # Estadual
    def test_spfl_2018(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/sao-paulo-football-league-2018/'], save_path=None)

        spfl_2012 = scrapper.scrape_tournaments(init=0, end=1)

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

    # Regional
    def test_nordeste_2019(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/copa-nordeste-2019/'], save_path=None)

        nordeste_2019 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(nordeste_2019) == 5

        bulls_patos = nordeste_2019[(nordeste_2019['Mandante'] == 'Bulls Potiguares 2') & (nordeste_2019['Visitante'] == 'Patos FA')]
        assert len(bulls_patos) == 1

        assert bulls_patos['Hor/Res'].iloc[0] == '31 - 23'
        assert bulls_patos['Data'].iloc[0] == '2019-04-28 15:00:00'


        redbulls_bulls = nordeste_2019[(nordeste_2019['Mandante'] == 'Santana Red Bulls') & (nordeste_2019['Visitante'] == 'Bulls Potiguares 2')]
        assert len(redbulls_bulls) == 1

        assert redbulls_bulls['Hor/Res'].iloc[0] == '25 - 14'
        assert redbulls_bulls['Data'].iloc[0] == '2019-08-10 18:00:00'

    # Nacional 3 - Esse aqui por algum motivo não tinha a formatação de sp-result ok x sp-result no resultado
    # Ajeitei o código pra pegar os 2 sp-results e colocar na ordem que aparece. Criei o teste pra isso
    def test_superliga_2015(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/superliga-nacional-2015/'], save_path=None)

        superliga_2015 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(superliga_2015) == 55

        roma_pirates = superliga_2015[(superliga_2015['Mandante'] == 'Roma Gladiadores') & (superliga_2015['Visitante'] == 'Santa Cruz Pirates')]
        assert len(roma_pirates) == 1

        assert roma_pirates['Hor/Res'].iloc[0] == '00 - 21'
        assert roma_pirates['Data'].iloc[0] == '2015-04-11 16:00:56'

        espectros_bulls = superliga_2015[(superliga_2015['Mandante'] == 'João Pessoa Espectros') & (superliga_2015['Visitante'] == 'América Bulls')]
        assert len(espectros_bulls) == 1

        assert espectros_bulls['Hor/Res'].iloc[0] == '21 - 03'
        assert espectros_bulls['Data'].iloc[0] == '2015-09-06 15:00:14'

        rednecks_cuiaba = superliga_2015[(superliga_2015['Mandante'] == 'Goiânia Rednecks') & (superliga_2015['Visitante'] == 'Cuiabá Arsenal')]
        assert len(rednecks_cuiaba) == 1

        assert rednecks_cuiaba['Hor/Res'].iloc[0] == '20 - 37'
        assert rednecks_cuiaba['Data'].iloc[0] == '2015-08-29 14:30:15'

        mariners_pirates = superliga_2015[(superliga_2015['Mandante'] == 'Recife Mariners') & (superliga_2015['Visitante'] == 'Recife Pirates')]
        assert len(mariners_pirates) == 1

        assert mariners_pirates['Hor/Res'].iloc[0] == '27 - 06'
        assert mariners_pirates['Data'].iloc[0] == '2015-11-08 15:00:14'

    #Estadual 1 - Esse aqui teve um jogo cancelado, que é o último assert. Testar isso ai
    def test_amazonense_2019(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/campeonato-amazonense-2019/'], save_path=None)

        amazonense_2019 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(amazonense_2019) == 4

        roma_pirates = amazonense_2019[(amazonense_2019['Mandante'] == 'North Lions') & (amazonense_2019['Visitante'] == 'Amazon Black Hawks')]
        assert len(roma_pirates) == 1

        assert roma_pirates['Hor/Res'].iloc[0] == '32 - 07'
        assert roma_pirates['Data'].iloc[0] == '2019-06-02 09:00:00'

        espectros_bulls = amazonense_2019[(amazonense_2019['Mandante'] == 'Manaus FA') & (amazonense_2019['Visitante'] == 'North Lions')]
        assert len(espectros_bulls) == 2

        assert espectros_bulls['Hor/Res'].iloc[1] == 'X - X'
        assert espectros_bulls['Data'].iloc[1] == '2019-06-30 00:00:00'

    #Estadual - Esse aqui a URL dá 404. Tô tendo ctz que quando isso acontecer, ele vai só retornar um df vazio,
    # e não um erro
    def test_matogrossense_2015(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/campeonato-matogrossense-2015/'], save_path=None)

        matogrossense_2015 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(matogrossense_2015) == 0

    # Esse aqui só tem tabela, n tem aqueles cards
    def test_mineiro_2012(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/campeonato-mineiro-2012/'], save_path=None)

        mineiro_2012 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(mineiro_2012) == 12

        locomotiva_gladiadores = mineiro_2012[(mineiro_2012['Mandante'] == 'América Locomotiva') & (mineiro_2012['Visitante'] == 'Pouso Alegre Gladiadores')]
        assert len(locomotiva_gladiadores) == 1

        assert locomotiva_gladiadores['Hor/Res'].iloc[0] == '54 - 00'
        assert locomotiva_gladiadores['Data'].iloc[0] == '2012-05-26 14:00:00'

    def test_copa_pr_2022(self):
        scrapper = GamesScrapper(['https://www.salaooval.com.br/campeonatos/copa-pr-2022/'], save_path=None)

        mineiro_2012 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(mineiro_2012) == 6

        locomotiva_gladiadores = mineiro_2012[(mineiro_2012['Mandante'] == 'São Miguel Indians') & (mineiro_2012['Visitante'] == 'Cascavel Olympians')]
        assert len(locomotiva_gladiadores) == 1

        assert locomotiva_gladiadores['Hor/Res'].iloc[0] == '19 - 00'
        assert locomotiva_gladiadores['Data'].iloc[0] == '2022-11-20 10:00:09'

    def test_taca_nove_2014(self):
        scrapper = GamesScrapper(['https://www.salaooval.com.br/campeonatos/taca-nove-de-julho-2014/'], save_path=None)

        taca_nove_2014 = scrapper.scrape_tournaments(init=0, end=1)

        assert len(taca_nove_2014) == 35

        mustangs_pouso = taca_nove_2014[(taca_nove_2014['Mandante'] == 'Avaré Mustangs') & (taca_nove_2014['Visitante'] == 'Pouso Alegre Gladiadores')]
        assert len(mustangs_pouso) == 1

        assert mustangs_pouso['Hor/Res'].iloc[0] == '06 - 12'
        assert mustangs_pouso['Data'].iloc[0] == '2014-10-25 14:00:00'

        cougars_vikings = taca_nove_2014[(taca_nove_2014['Mandante'] == 'Cougars Football') & (taca_nove_2014['Visitante'] == 'Vikings FA')]
        assert len(cougars_vikings) == 1

        assert cougars_vikings['Hor/Res'].iloc[0] == '18 - 19'
        assert cougars_vikings['Data'].iloc[0] == '2014-09-28 14:00:00'

        lizards_ocelots = taca_nove_2014[(taca_nove_2014['Mandante'] == 'Empyreo Leme Lizards') & (taca_nove_2014['Visitante'] == 'Ocelots FA')]
        assert len(lizards_ocelots) == 1

        assert lizards_ocelots['Hor/Res'].iloc[0] == '03 - 06'
        assert lizards_ocelots['Data'].iloc[0] == '2014-12-21 14:00:00'

    # Um dos 45 campeonatos que o script de scraping ignorou, por algum motivo que n sei dizer
    def test_bfa_2017(self):
        scrapper = GamesScrapper(['http://www.salaooval.com.br/campeonatos/bfa-2017/'], save_path=None)

        bfa_2017_df = scrapper.scrape_tournaments(init=0, end=1)

        assert len(bfa_2017_df) == 95

        cavalaria_mariners = bfa_2017_df[(bfa_2017_df['Mandante'] == 'Cavalaria 2 de Julho') & (bfa_2017_df['Visitante'] == 'Recife Mariners')]
        assert len(cavalaria_mariners) == 1

        assert cavalaria_mariners['Hor/Res'].iloc[0] == '00 - 34'
        assert cavalaria_mariners['Data'].iloc[0] == '2017-08-06 14:00:00'


        rex_mariners = bfa_2017_df[(bfa_2017_df['Mandante'] == 'Sada Cruzeiro') & (bfa_2017_df['Visitante'] == 'Flamengo Imperadores')]
        assert len(rex_mariners) == 1

        assert rex_mariners['Hor/Res'].iloc[0] == '26 - 07'
        assert rex_mariners['Data'].iloc[0] == '2017-08-05 18:00:00'


        rex_galo = bfa_2017_df[(bfa_2017_df['Mandante'] == 'Sada Cruzeiro') & (bfa_2017_df['Visitante'] == 'João Pessoa Espectros')]
        assert len(rex_galo) == 1

        assert rex_galo['Hor/Res'].iloc[0] == '30 - 13'
        assert rex_galo['Data'].iloc[0] == '2017-12-10 17:00:42'

        
        

    def test_two_leagues(self):
        urls_list = ['http://www.salaooval.com.br/campeonatos/bfa-2024/', 'http://www.salaooval.com.br/campeonatos/campeonato-brasileiro-2012/']

        scrapper = GamesScrapper(urls_list, save_path=None)

        all_games = scrapper.scrape_tournaments(init=0, end=2)

        assert len(all_games) == 160

        bfa_2024 = all_games[all_games['Torneio'] == 'bfa-2024']
        brasileiro_2012 = all_games[all_games['Torneio'] == 'campeonato-brasileiro-2012']

        assert len(bfa_2024) == 52
        assert len(brasileiro_2012) == 108





