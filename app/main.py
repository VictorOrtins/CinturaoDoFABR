import os

import streamlit as st

from utils.page_utils import set_background_color
from utils.data_utils import read_csv_data, read_image_from_url, resize_img

games_df = read_csv_data(os.path.join('data', 'cinturao', 'games.csv'))
teams_df = read_csv_data(os.path.join('data','teams', 'teams.csv'))

atual_detentor = games_df.iloc[-1]['Vencedor']
atual_detentor_df = teams_df[teams_df['Nome'] == atual_detentor]
page_color = atual_detentor_df['Cor Primária'].iloc[0]
atual_detentor_url = atual_detentor_df['URL da Imagem'].iloc[0]

# set_background_color(page_color)


page = st.navigation([st.Page(os.path.join("pages", "inicio.py"), title="Home", icon="🏆"), st.Page(os.path.join("pages", "regras.py"), title="Regras", icon="📜"), st.Page(os.path.join("pages", "stats.py"), title="Estatísticas", icon="📊")])
page.run()
