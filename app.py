import streamlit as st
import pytesseract
from PIL import Image
import re

# Configuration de la page
st.set_page_config(page_title="Outils DYS", page_icon="✏️", layout="wide")

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

def colorize_complex_sounds(text):
    """Mise en valeur des sons complexes fréquents (ch, ph, ou, an, en, in, on, un, etc.)"""
    pattern = r'(ou|an|en|in|on|un|ch|ph|gn|ei|ai|au|eu|oin|ien|eau)'
    def replace_fn(match):
        return f"<span style='color: #e67e22; font-weight: bold;'>{match.group(0)}</span>"
    return re.sub(pattern, replace_fn, text, flags=re.IGNORECASE)

def colorize_letters(text):
    """Mise en valeur des voyelles / lettres complexes pour aider au décodage"""
    vowels = {'a': '#cc0000', 'e': '#0055ff', 'i': '#00aa00', 'o': '#ff6600', 'u': '#9900cc', 'y': '#00aa00'}
    res = []
    for char in text:
        lower_char = char.lower()
        if lower_char in vowels:
            color = vowels[lower_char]
            res.append(f"<span style='color: {color}; font-weight: bold;'>{char}</span>")
        else:
            res.append(char)
    return "".join(res)

def make_syllable_arcs(text):
    """Ajoute des ponts visuels sous les découpages de syllabes"""
    words = text.split()
    res_words = []
    for word in words:
        if len(word) <= 3:
            res_words.append(f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{word}</span>")
        else:
            parts = re.findall(r'.{1,2}(?=[aeiouyàâéèêëîïôûùü]|$)', word, flags=re.IGNORECASE)
            if parts:
                arcs = " ‿ ".join([f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{p}</span>" for p in parts])
                res_words.append(arcs)
            else:
                res_words.append(f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{word}</span>")
    return " ".join(res_words)

def render_dys_text(text, mode, size, spacing):
    if not text:
        return
    style = f"font-size: {size}px; line-height: {spacing};"
    
    if mode == "Coloration des sons complexes":
        content = colorize_complex_sounds(text).replace('\n', '<br>')
    elif mode == "Coloration des lettres / voyelles":
        content = colorize_letters(text).replace('\n', '<br>')
    elif mode == "Ponts et découpage syllabique":
        content = make_syllable_arcs(text).replace('\n', '<br>')
    elif mode == "Alternance des mots (Bleu / Rouge)":
        words = text.split()
        res = []
        for i, w in enumerate(words):
            c = "#0055ff" if i % 2 == 0 else "#cc0000"
            res.append(f"<span style='color: {c}; font-weight: bold;'>{w}</span>")
        content = " ".join(res)
    elif mode == "Alternance des lignes":
        lines = text.split('\n')
        res = []
        for i, l in enumerate(lines):
            c = "#0055ff" if i % 2 == 0 else "#cc0000"
            res.append(f"<div style='color: {c}; margin-bottom: 6px;'>{l}</div>")
        content = "".join(res)
    elif mode == "Surlignage doux":
        content = f"<div style='background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2;'>{text}</div>"
    else:
        content = text.replace('\n', '<br>')
        
    st.markdown(f"<div style='{style}'>{content}</div>", unsafe_allow_html=True)

# --- ONGLET 1 : Saisie directe ---
with tab1:
    st.write("### Saisir ou coller un texte")
    txt = st.text_area("Entrez votre texte :", height=140, placeholder="Tapez ou collez votre texte...")
    if txt:
        st.write("---")
        st.write("### ⚙️ Options de mise en page DYS")
        col1, col2 = st.columns(2)
        with col1:
            m = st.selectbox(
                "Option pédagogique :",
                [
                    "Aucun",
                    "Coloration des sons complexes",
                    "Coloration des lettres / voyelles",
                    "Ponts et découpage syllabique",
                    "Alternance des mots (Bleu / Rouge)",
                    "Alternance des lignes",
                    "Surlignage doux"
                ],
                key="t1_m"
            )
        with col2:
            s = st.slider("Taille de police (px) :", 14, 32, 22, key="t1_s")
            sp = st.slider("Espacement des lignes :", 1.2, 3.0, 2.0, 0.1, key="t1_sp")
        
        st.write("### 👁️ Aperçu adapté :")
        render_dys_text(txt, m, s, sp)

# --- ONGLET 2 : Image & OCR ---
with tab2:
    st.write("### Importer une image")
    file = st.file_uploader("Choisissez une image (PNG, JPG)", type=["png", "jpg", "jpeg"])
    if file:
        img = Image.open(file)
        st.image(img, caption="Image importée", use_container_width=True)
        try:
            ext_txt = pytesseract.image_to_string(img, lang="fra")
            if ext_txt.strip():
                st.success("Texte extrait avec succès !")
                st.write("---")
                st.write("### ⚙️ Options de mise en page DYS pour le texte extrait")
                col1, col2 = st.columns(2)
                with col1:
                    m2 = st.selectbox(
                        "Option pédagogique :",
                        [
                            "Aucun",
                            "Coloration des sons complexes",
                            "Coloration des lettres / voyelles",
                            "Ponts et découpage syllabique",
                            "Alternance des mots (Bleu / Rouge)",
                            "Alternance des lignes",
                            "Surlignage doux"
                        ],
                        key="t2_m"
                    )
                with col2:
                    s2 = st.slider("Taille de police (px) :", 14, 32, 22, key="t2_
