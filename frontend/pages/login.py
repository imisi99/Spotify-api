# import streamlit as st
#
# st.header("Log in to Dashie")
#
# st.write("login using spotify")
# auth_url = "https://spotify-dv92.onrender.com/user/login"
#
# def login():
#     if st.button("login"):
#         st.markdown(f'<meta http-equiv="refresh" content="0;URL={auth_url}">', unsafe_allow_html=True)
#
# login()
#
# st.write("You need to have a spotify account to continue")


import streamlit as st

st.header("Log in to Dashie")

st.write("Login using Spotify")

# Inject custom HTML and JavaScript
st.components.v1.html(
    """
    <button id="login-button">Login with Spotify</button>
    <script>
        document.getElementById("login-button").addEventListener("click", function() {
            // Make a fetch request to your FastAPI backend
            fetch("https://spotify-dv92.onrender.com/user/login", {
                method: "GET",
                credentials: "include"  // Include cookies in the request
            })
            .then(response => {
                if (response.redirected) {
                    // Redirect the user to the Spotify authorization page
                    window.location.href = response.url;
                }
            })
            .catch(error => {
                console.error("Error:", error);
            });
        });
    </script>
    """,
    height=100,  # Adjust height as needed
)

st.write("You need to have a Spotify account to continue.")