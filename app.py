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

# Menu de sélection du mode
tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

with tab1:
    st.write("### Saisir ou coller un texte à adapter")
    user_text = st.text_area("Entrez votre texte ici :", height=200, placeholder="Tapez ou collez votre texte pédagogique...")
    
    if user_text:
        st.write("---")
        st.write("### Options de mise en page DYS")
        
        # Choix de la couleur pour les mots ou alternance
        color_choice = st.selectbox(
            "Choisissez un code couleur pour le texte :",
            ["Aucun", "Alternance des mots (Bleu / Rouge)", "Mise en valeur (Surlignage doux)"]
        )
        
        st.write("### Aperçu adapté :")
        
        if color_choice == "Alternance des mots (Bleu / Rouge)":
            words = user_text.split()
            colored_words = []
            for i, word in enumerate(words):
                if i % 2 == 0:
                    colored_words.append(f"<span style='color: #0066cc; font-weight: bold;'>{word}</span>")
                else:
                    colored_words.append(f"<span style='color: #cc0000; font-weight: bold;'>{word}</span>")
            formatted_html = f"<p style='font-size: 20px; line-height: 1.8;'>{' '.join(colored_words)}</p>"
            st.markdown(formatted_html, unsafe_allow_html=True)
            
        elif color_choice == "Mise en valeur (Surlignage doux)":
            formatted_html = f"<p style='font-size: 20px; line-height: 1.8; background-color: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #4a90e2;'>{user_text}</p>"
            st.markdown(formatted_html, unsafe_allow_html=True)
        else:
            st.write(user_text)

with tab2:
    st.write("### Importer un document ou une image")
    uploaded_file = st.file_uploader("Choisissez une image (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Document importé", use_container_width=True)
        
        if st.button("🔍 Extraire le texte (OCR)"):
            with st.spinner("Analyse du texte en cours..."):
                try:
                    extracted_text = pytesseract.image_to_string(image, lang="fra")
                    if extracted_text.strip():
                        st.success("Texte extrait avec succès !")
                        st.text_area("Texte détecté :", extracted_text, height=250)
                    else:
                        st.warning("Aucun texte lisible n'a été trouvé.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

# Pied de page
st.write("---")
st.caption("Application développée pour l'adaptation de documents pédagogiques.")
