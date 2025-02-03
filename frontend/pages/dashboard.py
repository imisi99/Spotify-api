import streamlit as st
import requests

p_uri = "https://spotify-dv92.onrender.com/user/profile"
def get_details():
    request = requests.get(p_uri)
    return request.status_code

value = get_details()

st.write(value)