import os

import streamlit as st

page = st.navigation(
    [
        st.Page(os.path.join("pages", "inicio.py"), title="Home", icon="🏆"),
        st.Page(os.path.join("pages", "regras.py"), title="Regras", icon="📜"),
        st.Page(os.path.join("pages", "stats.py"), title="Estatísticas", icon="📊"),
        st.Page(os.path.join("pages", "jogos.py"), title="Jogos do Cinturão", icon="🏈")
    ]
)
page.run()
