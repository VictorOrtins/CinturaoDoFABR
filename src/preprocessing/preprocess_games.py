import os

from preprocessor import Preprocessor

if __name__ == '__main__':
    preprocessor = Preprocessor()

    preprocessor.read_data_in_folder(os.path.join('data', 'raw'))

    final_games_df = preprocessor.preprocess_games_df()

    final_games_df.to_csv(os.path.join('data', 'preprocessed', 'games.csv'), index=False)


