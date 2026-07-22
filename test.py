from oauth_google import login_google
import streamlit as st

auth_url = login_google()

st.link_button("Open Google", auth_url)

st.markdown(
    f'<a href="{auth_url}" target="_blank">HTML Link</a>',
    unsafe_allow_html=True,
)

st.code(auth_url)