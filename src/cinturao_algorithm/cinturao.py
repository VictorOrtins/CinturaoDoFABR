import pandas as pd

class Cinturao:
    def __init__(self, preprocessed_games_path: str):
        self.path = preprocessed_games_path
        self.games_df = None

    def read_games_data(self):
        self.games_df = pd.read_csv(self.path)

    def run_cinturao_algorithm(self) -> pd.DataFrame:
        if self.games_df is None:
            raise RuntimeError("Primeiro rode read_games_data para que os jogos sejam armazenados na classe")

        current_game = self.games_df.iloc[0]
        current_champion = current_game['Vencedor']
        current_game_date = current_game['Data']
        cinturao_games = pd.DataFrame([current_game], index=None)

        while True:
            try:
                current_game = self.games_df[ ((self.games_df['Mandante'] == current_champion) | (self.games_df['Visitante'] == current_champion)) & (self.games_df['Data'] > current_game_date) ].iloc[0]
            except IndexError:
                break
            
            current_champion = current_game['Vencedor']
            current_game_date = current_game['Data']

            cinturao_games = pd.concat([cinturao_games, current_game.to_frame().T], ignore_index=True)

        return cinturao_games
    

if __name__ == '__main__':
    cinturao = Cinturao(preprocessed_games_path='data/preprocessed/games.csv')

    cinturao.read_games_data()

    cinturao_games = cinturao.run_cinturao_algorithm()

    cinturao_games.to_csv('data/cinturao/games.csv', index=False)