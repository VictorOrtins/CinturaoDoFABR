import streamlit as st

from PIL import Image

from utils.data_utils import read_image_from_url

def set_background_color(color):
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {color} !important;
                background-image: none !important;
            }}
            div[data-testid="stSidebar"] {{
                background-color: {color} !important;
            }}
            .block-container {{
                background-color: {color} !important;
                padding: 2rem;
                border-radius: 15px;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

@st.cache_data
def get_image_from_url(url: str) -> Image:
    return read_image_from_url(url)

@st.cache_data
def display_video(url: str):
    st.video(url)