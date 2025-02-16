import streamlit as st

st.header("Log in to Dashie")

st.write("login using your spotify account")
auth_url = "https://spotify-dv92.onrender.com/user/login"


st.link_button("Log in", auth_url)
st.write("You need to have a spotify account to continue")

