import streamlit as st
import time

# st.title("AltSchool Spotify API")
# val ="Welcome Imisioluwa to a whole new world"
#
#
# lc, rc = st.columns(2)
#
# val
# x = st.sidebar.slider('squared')
# st.write(x, 'squared is', x * x)
#
# lc.text_input("Enter your name", key="username")
#
# if st.sidebar.checkbox('Display name'):
#     st.session_state.username
#
# cars = ['cyber_truck', 's model']
#
# option = st.sidebar.selectbox('Choose a car', cars)
#
# 'You selected: ', option
#
#
# lc.button('Press me!')
# with rc:
#     chosen = st.radio('Which car?', cars)
#     st.write(f"you selected: {chosen}")

# 'Starting a long computation'
#
# latest_iteration = st.empty()
# bar = st.progress(0)
#
# for i in range(100):
#     latest_iteration.text(f"Progress {i+1}")
#     bar.progress(1 + i)
#
# 'done'
#
# def page_view():
#     if "counter" not in st.session_state:
#         st.session_state.counter = 0
#
#     st.session_state.counter += 1
#     val = st.session_state.counter
#     return val
#
#
# f"This page has been viewed {page_view()} times"
# st.button("Run again")

st.sidebar.markdown("Main Page")