import streamlit as st
import httpx

p_uri = "http://localhost:8000/user/get_cookies"

with httpx.Client() as session:
    response = session.get(p_uri)
    try:
        st.write(response.json())
    except httpx.HTTPStatusError:
        st.write({"error": "Could not get details", "status_code": response.status_code, "test": response.text})

