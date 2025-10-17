# pages/Logout.py
import streamlit as st
st.title("Logging out...")
if st.button("Logout now"):
    st.session_state.clear()
    st.experimental_rerun()
