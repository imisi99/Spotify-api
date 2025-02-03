import streamlit as st

st.header("Log in to Dashie")

st.write("login using spotify")
auth_url = "https://spotify-dv92.onrender.com/user/login"


if st.button("login"):
    st.markdown(f'<meta http-equiv="refresh" content="0;URL={auth_url}">', unsafe_allow_html=True)


st.write("You need to have a spotify account to continue")

