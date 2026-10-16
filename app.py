import streamlit as st
import traceback

try:
    import application_mathis
except Exception:
    st.error("Une erreur empêche le chargement de Mathis.")
    st.code(traceback.format_exc())
