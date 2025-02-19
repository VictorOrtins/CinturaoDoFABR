import os

import streamlit as st

from utils.data_utils import read_csv_data, get_img_url

st.set_page_config(layout="wide")

st.title("Jogos valendo o cinturão")

st.text("Aqui estão listados todos os jogos valendo o cinturão do FABR, do seu início até o fim")

st.text("A tabela é interativa, então ordene-a como desejar. Há também uma ferramenta de busca, caso queira.")

base_dir = os.path.dirname(os.path.abspath(__file__))

games_df = read_csv_data(os.path.join(base_dir, "..", 'data', 'cinturao', 'games.csv'))
games_df = games_df.drop(columns=['Campo', 'Fase', 'Pontos Mandante', 'Pontos Visitante'])
games_df.columns = ['Data', 'Mandante', 'Resultado', 'Visitante', 'Torneio', 'Vencedor', 'Defensor do Cinturão']

teams_df = read_csv_data(os.path.join(base_dir, "..", 'data', 'teams', 'teams.csv'))
games_df['URL Mandante'] = games_df['Mandante'].apply(lambda x: get_img_url(x, teams_df))
games_df['URL Visitante'] = games_df['Visitante'].apply(lambda x: get_img_url(x, teams_df))

games_df = games_df[['Data', 'URL Mandante', 'Mandante', 'Resultado', 'URL Visitante', 'Visitante', 'Torneio', 'Vencedor', 'Defensor do Cinturão']]
games_df['Data'] = games_df['Data'].apply(lambda x: x[:10])

row_height = 35
height = (len(games_df) + 1) * row_height

st.dataframe(games_df,
             column_config={
                 "URL Mandante": st.column_config.ImageColumn(" ", width="small"),
                 "URL Visitante": st.column_config.ImageColumn(" ", width="small")
             },
             hide_index=True, 
             height=height, 
             use_container_width=True)

