from enum import Enum
import os

import pandas as pd
pd.options.mode.chained_assignment = None

# Trocar Joinville Gladiators por JEC Gladiators
class Preprocessor:
    class Regiao(Enum):
        SUDESTE = 'sudeste'
        NORDESTE = 'nordeste'
        SUL = 'sul'
        NORTE = 'norte'
        CENTRO_OESTE = 'centro-oeste'

    def __init__(self):
        self.original_teams_df: pd.DataFrame = None
        self.final_teams_df: pd.DataFrame

    def read_data_in_folder(self, folder_path: str) -> pd.DataFrame:
        if not os.path.isdir(folder_path):
            raise ValueError("Folder path needs to exist")

        folder_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

        teams_files = [file for file in folder_files if 'teams' in file]

        teams_df = pd.concat((pd.read_csv(file) for file in teams_files), ignore_index=True)

        self.original_teams_df = teams_df

        return teams_df
    
    def preprocess_teams_df(self):
        original_teams_df = self.original_teams_df.copy()

        teams_df = self.__remove_special_characters(original_teams_df)

        teams_df = original_teams_df.drop_duplicates(subset=['Nome'])

        teams_df = self.__fix_teams_names(teams_df)

        teams_df = self.__fix_sede(teams_df)

        teams_df = self.__add_state_column(teams_df)

        teams_df = self.__add_regiao_column(teams_df)

        self.final_teams_df = teams_df.copy()

        return self.final_teams_df
    
    def __remove_special_characters(self, teams_df: pd.DataFrame) -> pd.DataFrame:
        teams_df['Nome'] = teams_df['Nome'].str.replace(r'\s+', ' ', regex=True).str.strip()

        return teams_df
    
    def __fix_teams_names(self, teams_df: pd.DataFrame) -> pd.DataFrame:
        teams_df['Nome'] = teams_df['Nome'].str.replace('Joinville Gladiators', 'JEC Gladiators').str.strip()
        teams_df['Nome'] = teams_df['Nome'].str.replace('Galo Futebol Americano', 'Sada Cruzeiro/Galo FA').str.strip()

        return teams_df
    
    def __fix_sede(self, original_teams_df: pd.DataFrame) -> pd.DataFrame:
        original_teams_df['Sede'] = original_teams_df['Sede'].apply(lambda x: None if x == 's' else x)

        return original_teams_df
    
    def __add_state_column(self, teams_df: pd.DataFrame) -> pd.DataFrame:
        teams_df['Estado'] = teams_df['Sede'].apply(lambda x: x.split('/')[-1] if isinstance(x, str) else x)

        return teams_df

    
    def __add_regiao_column(self, teams_df: pd.DataFrame) -> pd.DataFrame:
        teams_df = teams_df.apply(lambda x: self.__insert_regiao(x), axis=1)

        return teams_df

    def __insert_regiao(self, row: pd.Series) -> pd.Series:
        estados_regiao = {
            'AC': self.Regiao.NORTE,
            'AM': self.Regiao.NORTE,
            'RR': self.Regiao.NORTE,
            'AP': self.Regiao.NORTE,
            'PA': self.Regiao.NORTE,
            'RO': self.Regiao.NORTE,
            'TO': self.Regiao.NORTE,

            'MA': self.Regiao.NORDESTE,
            'PI': self.Regiao.NORDESTE,
            'CE': self.Regiao.NORDESTE,
            'RN': self.Regiao.NORDESTE,
            'PB': self.Regiao.NORDESTE,
            'PE': self.Regiao.NORDESTE,
            'AL': self.Regiao.NORDESTE,
            'SE': self.Regiao.NORDESTE,
            'BA': self.Regiao.NORDESTE,

            'DF': self.Regiao.CENTRO_OESTE,
            'MT': self.Regiao.CENTRO_OESTE,
            'GO': self.Regiao.CENTRO_OESTE,
            'MS': self.Regiao.CENTRO_OESTE,

            'MG': self.Regiao.SUDESTE,
            'SP': self.Regiao.SUDESTE,
            'ES': self.Regiao.SUDESTE,
            'RJ': self.Regiao.SUDESTE,

            'PR': self.Regiao.SUL,
            'SC': self.Regiao.SUL,
            'RS': self.Regiao.SUL
        }
        estado = row['Estado']

        if not isinstance(estado, str):
            row['Regiao'] = None
            return row

        regiao = estados_regiao[estado].value

        row['Regiao'] = regiao

        return row
    
if __name__ == '__main__':
    preprocessor = Preprocessor()

    unpreprocessed_teams_df = preprocessor.read_data_in_folder('data')
    print(len(unpreprocessed_teams_df))

    final_teams_df = preprocessor.preprocess_teams_df()
    print(len(final_teams_df))

    print(final_teams_df.head())

