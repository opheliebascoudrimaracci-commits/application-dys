import streamlit as st
import pytesseract
from PIL import Image

# Configuration de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci - Outils Pédagogiques",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

st.markdown("""
Bienvenue sur l'application d'adaptation de supports pédagogiques. 
Téléchargez un document ou une image pour adapter la mise en page, extraire le texte ou préparer un exercice.
""")

# Zone de téléversement de fichier
uploaded_file = st.file_uploader(
    "Choisissez un fichier (Image PNG, JPG ou Document)", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Document importé", use_container_width=True)
    
    st.write("---")
    st.write("### Options de traitement")
    
    if st.button("🔍 Extraire le texte (OCR)"):
        with st.spinner("Analyse du texte en cours..."):
            try:
                extracted_text = pytesseract.image_to_string(image, lang="fra")
                if extracted_text.strip():
                    st.success("Texte extrait avec succès !")
                    st.text_area("Texte détecté :", extracted_text, height=250)
                else:
                    st.warning("Aucun texte lisible n'a été trouvé dans cette image.")
            except Exception as e:
                st.error(f"Erreur lors de la lecture de l'image : {e}")

# Pied de page
st.write("---")
st.caption("Application développée pour la gestion et l'adaptation de documents pédagogiques.")
