import os
import sys

import streamlit as st

base_dir = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.abspath(os.path.join(base_dir, '..'))
sys.path.append(project_path)

from utils.data_utils import read_csv_data  # noqa: E402
from utils.visualization_utils import (  # noqa: E402
    get_most_cinturao_defenses,
    get_most_cinturao_wins,
    get_teams_with_most_games,
    get_teams_with_most_losses,
    get_teams_with_most_cinturao_losses,
    get_teams_with_most_days_with_cinturao,
    get_teams_with_most_consecutive_days_with_cinturao
)

base_dir = os.path.dirname(os.path.abspath(__file__))

stats = {
    "Times com mais Defesas de Títulos": get_most_cinturao_defenses,
    "Times com mais conquistas do Cinturão": get_most_cinturao_wins,
    "Times que mais jogaram em partidas valendo o cinturão": get_teams_with_most_games,
    "Times que mais perderam jogos valendo o Cinturão": get_teams_with_most_losses,
    "Times com mais perdas do Cinturão": get_teams_with_most_cinturao_losses,
    "Times que mais tempo ficaram com o Cinturão": get_teams_with_most_days_with_cinturao,
    "Times que mais tempo ficaram com o Cinturão consecutivamente": get_teams_with_most_consecutive_days_with_cinturao,
    "Times que mais partidas consecutivamente ficaram com o Cinturão": get_most_cinturao_defenses,
}


st.title("Estatísticas Relevantes")

games_df = read_csv_data(os.path.join(base_dir, "..", "data", "cinturao", "games.csv"))
teams_df = read_csv_data(os.path.join(base_dir, "..", "data", "teams", "teams.csv"))

option = st.selectbox(
    "Qual Estatística deseja ver?",
    tuple(stats.keys()),
    index=None,
    placeholder="Escolha a estatística",
)

if option is not None:
    st.header(option)

    figure = stats[option](games_df, teams_df)
    st.plotly_chart(figure, use_container_width=True)
