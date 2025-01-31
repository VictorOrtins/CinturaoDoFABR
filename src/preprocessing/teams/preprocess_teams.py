import os

from preprocessor import Preprocessor

if __name__ == '__main__':
    preprocessor = Preprocessor()

    preprocessor.read_data_in_folder(os.path.join('data', 'teams', 'raw'))

    final_games_df = preprocessor.preprocess_teams_df()

    final_games_df.to_csv(os.path.join('data', 'teams', 'preprocessed', 'teams.csv'), index=False)


