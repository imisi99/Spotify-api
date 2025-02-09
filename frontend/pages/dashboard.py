import streamlit as st
import requests

p_uri = "http://localhost:8000/user/profile"
def get_details():
    request = requests.get(p_uri)
    try:
        return request.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": "Could not get details", "status_code": request.status_code, "test": request.text}

value = get_details()

st.write(value)