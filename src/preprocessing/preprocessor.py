import os

import pandas as pd


class Preprocessor:
    def __init__(self):
        self.original_games_df: pd.DataFrame = None
        self.final_games_df: pd.DataFrame

    def read_data_in_folder(self, folder_path: str) -> pd.DataFrame:
        if not os.path.isdir(folder_path):
            raise ValueError("Folder path needs to exist")

        folder_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

        games_files = [file for file in folder_files if 'games' in file]

        games_df = pd.concat((pd.read_csv(file) for file in games_files), ignore_index=True)

        self.original_games_df = games_df

        return games_df
    
    def preprocess_games_df(self):
        original_games_df = self.original_games_df.copy()

        games_df = self.__fix_teams_names(original_games_df)

        games_df = self.__remove_zero_column(games_df)

        games_df = self.__remove_temporada_column(games_df)

        games_df = self.__remove_duplicate_games(games_df)

        games_df = self.__split_result_column(games_df)

        games_df = self.__remove_unplayed_matches(games_df)

        games_df = self.__add_match_winner_column(games_df)

        games_df = self.__order_by_oldest_games(games_df)

        self.final_games_df = games_df.copy()

        return self.final_games_df

    def __remove_zero_column(self, games_df: pd.DataFrame):
        return self.__remove_column(games_df, '0')
    
    def __remove_temporada_column(self, games_df: pd.DataFrame):
        return self.__remove_column(games_df, 'Temporada')
    
    def __remove_column(self, games_df: pd.DataFrame, column: str):
        if column not in games_df.columns:
            return games_df
        
        zero_column_values = games_df[column].value_counts().index.to_list()

        games_df = games_df[~games_df[column].isin(zero_column_values)]
        games_df = games_df.drop(columns=[column])

        return games_df

    def __remove_duplicate_games(self, games_df: pd.DataFrame):
        games_df = games_df.drop_duplicates(subset=['Data', 'Mandante', 'Hor/Res', 'Visitante', 'Torneio'])
        return games_df
          
    def __split_result_column(self, games_df: pd.DataFrame):
        games_df = games_df.apply(self.__split_mandante_visitante, axis=1)
        return games_df

    def __split_mandante_visitante(self, row):
        hor_res = row['Hor/Res']
        error = False
        try:
            pontos_mandante = int(hor_res.split(' - ')[0])
        except Exception:
            error = True

        try:
            pontos_visitante = hor_res.split(' - ')[1]
            if pontos_visitante.endswith('*'):
                pontos_visitante = pontos_visitante.split('*')[0]
            
            pontos_visitante = int(pontos_visitante)
        except Exception:
            error = True

        if error:
            row['Pontos Mandante'] = 'X'
            row['Pontos Visitante'] = 'X'
            return row

        row['Pontos Mandante'] = pontos_mandante
        row['Pontos Visitante'] = pontos_visitante

        return row
    
    def __remove_unplayed_matches(self, games_df: pd.DataFrame):
        games_df = games_df[ (games_df['Pontos Mandante'] != 'X') | (games_df['Pontos Visitante'] != 'X')]
        return games_df
    
    def __add_match_winner_column(self, games_df: pd.DataFrame):
        games_df['Vencedor'] = games_df.apply(self.__get_match_winner, axis=1)
        return games_df

    def __get_match_winner(self, row):
        pontos_mandante = row['Pontos Mandante']
        pontos_visitante = row['Pontos Visitante']

        if self.__jogo_anulado(pontos_mandante, pontos_visitante):
            vencedor = 'X'
        elif self.__empate(pontos_mandante, pontos_visitante):
            vencedor = 'Empate'
        elif self.__vitoria_mandante(pontos_mandante, pontos_visitante):
            vencedor = row['Mandante']
        elif self.__vitoria_visitante(pontos_mandante, pontos_visitante):
            vencedor = row['Visitante']

        return vencedor
    
    def __jogo_anulado(self, pontos_mandante, pontos_visitante):
        return pontos_mandante == 'X' and pontos_visitante == 'X'
    
    def __empate(self, pontos_mandante, pontos_visitante):
        return pontos_mandante == pontos_visitante
    
    def __vitoria_mandante(self, pontos_mandante, pontos_visitante):
        return pontos_mandante > pontos_visitante
    
    def __vitoria_visitante(self, pontos_mandante, pontos_visitante):
        return pontos_mandante < pontos_visitante
    
    def __order_by_oldest_games(self, games_df: pd.DataFrame):
        games_df = games_df.sort_values(by=['Data'], ascending=True)
        return games_df
    
    def __fix_teams_names(self, games_df: pd.DataFrame):
        games_df['Mandante'] = games_df['Mandante'].apply(lambda x: self.__fix_names(x))
        games_df['Visitante'] = games_df['Visitante'].apply(lambda x: self.__fix_names(x))

        return games_df
    
    def __fix_names(self, team_name: str):
        if team_name == 'Sada Cruzeiro' or team_name == 'Galo FA':
            return 'Sada Cruzeiro/Galo FA'
        
        return team_name
    

if __name__ == '__main__':
    preprocessor = Preprocessor()

    unpreprocessed_games_df = preprocessor.read_data_in_folder('data')
    print(len(unpreprocessed_games_df))

    final_games_df = preprocessor.preprocess_games_df()
    print(len(final_games_df))

