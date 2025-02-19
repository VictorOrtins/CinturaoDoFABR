import os

import streamlit as st

from utils.page_utils import set_background_color, get_image_from_url, display_video
from utils.data_utils import read_csv_data

print(os.listdir())
print(os.listdir('data'))
games_df = read_csv_data(os.path.join('data', 'cinturao', 'games.csv'))
teams_df = read_csv_data(os.path.join('data','teams', 'teams.csv'))

atual_detentor = games_df.iloc[-1]['Vencedor']
atual_detentor_df = teams_df[teams_df['Nome'] == atual_detentor]
atual_detentor_url = atual_detentor_df['URL da Imagem'].iloc[0]

st.markdown(
    "<h1 style='text-align: center; white-space: nowrap;'>Cinturão do Futebol Americano Brasileiro</h1>",
    unsafe_allow_html=True,
)

st.header("O que é o Cinturão do FABR")

st.text(
    "E se o futebol americano brasileiro fosse estruturado de uma maneira completamente diferente? " +  
    "Em vez de títulos decididos por temporadas e playoffs, o campeão só poderia ser coroado ao derrotar o atual detentor do" 
    + "cinturão. Nesse modelo, inspirado no boxe, a equipe que conquista o título precisa defendê-lo a cada jogo" 
    "contra novos desafiantes, tornando cada partida uma verdadeira disputa pelo domínio do esporte"
)

st.text(
    "Essa é a essência do Cinturão do Futebol Americano Brasileiro: um título que não se ganha em uma temporada perfeita" 
    " ou em um torneio eliminatório, mas sim no campo, jogo após jogo, com cada campeão precisando provar sua superioridade" 
    "todas as vezes que entrar em campo."
)

st.text("A primeira partida considerada para o cinturão não poderia ser outra: o FABR Day. No dia 25 de outubro de 2008 " + 
        "Curitiba Brown Spiders (hoje só Brown Spiders) e Barigui Crocodiles (hoje Coritiba Crocodiles) protagonizaram o primeiro" + 
        " jogo full pad em solo brasileiro. Venceu o Brown Spiders, que se sagrou o primeiro detentor do Cinturão do FABR")

st.text("As próximas partidas consideradas para o cinturão foram apenas em torneios oficiais. Sendo assim, o Brown Spiders " + 
        "defendeu o cinturão no jogo seguinte no dia 07 de agosto de 2009, contra o Joinville Gladiators e venceu, mantendo o título")

st.text("Na partida seguinte, porém, em 22 de agosto de 2009, o Coritiba Crocodiles derrotou o Brown Spiders por 23x20 e " + 
        "se sagrou o novo detentor do cinturão do FABR. E assim, se sucedeu, até o presente, em que o Recife Mariners é o atual detentor")

atual_campeao_col, _, ultima_disputa_col= st.columns([5, 0.3, 5])

with atual_campeao_col:
    st.header("Atual Detentor 🏆")
    atual_campeao_img = get_image_from_url(atual_detentor_url)
    st.image(atual_campeao_img, use_container_width=True)

with ultima_disputa_col:
    st.header("Última Disputa 🎥")
    display_video("https://www.youtube.com/watch?v=MIpNXE26qHw&t=426s")
