import streamlit as st
import requests

p_uri = "https://spotify-dv92.onrender.com/user/get_cookies"

session = requests.Session()
response = session.get(p_uri)
st.write(response.json())