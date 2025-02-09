import streamlit as st

st.header("Log in to Dashie")

st.write("login using your spotify account")
auth_url = "http://localhost:8000/user/login"


st.link_button("Log in", auth_url)
st.write("You need to have a spotify account to continue")

