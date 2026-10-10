import streamlit as st
import pytesseract
from PIL import Image
import re

st.set_page_config(
    page_title="Ophélie Bascou Drimaracci - Outils Pédagogiques",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

def colorize_complex_sounds(text):
    pattern = r'(ou|an|en|in|on|un|ch|ph|gn|ei|ai|au|eu|oin|ien|eau)'
    def replace_fn(m):
        return f"<span style='color: #e67e22; font-weight: bold;'>{m.group(0)}</span>"
    return re.sub(pattern, replace_fn, text, flags=re.IGNORECASE)

def colorize_letters(text):
    vowels = {'a': '#cc0000', 'e': '#0055ff', 'i': '#00aa00', 'o': '#ff6600', 'u': '#9900cc', 'y': '#00aa00'}
    res = []
    for char in text:
        lc = char.lower()
        if lc in vowels:
            res.append(f"<span style='color: {vowels[lc]}; font-weight: bold;'>{char}</span>")
        else:
            res.append(char)
    return "".join(res)

def make_syllable_arcs(text):
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
            
    html_output = f"<div style='font-size: {size}px; line-height: {spacing};'>{content}</div>"
    st.markdown(html_output, unsafe_allow_html=True)

opts = [
    "Aucun",
    "Coloration des sons complexes",
    "Coloration des lettres / voyelles",
    "Ponts et découpage syllabique",
    "Alternance des mots (Bleu / Rouge)",
    "Alternance des lignes",
    "Surlignage doux"
]

with tab1:
    st.write("### Saisir ou coller un texte")
    txt = st.text_area("Entrez votre texte ici :", height=140, placeholder="Tapez ou collez votre texte pédagogique...")
    if txt:
        st.write("---")
        st.write("### ⚙️ Options de mise en page DYS & Phonétique")
        c1, c2 = st.columns(2)
        with c1:
            m1 = st.selectbox("Option pédagogique :", opts, key="k_m1")
        with c2:
            s1 = st.slider("Taille de police (px) :", 14, 32, 22, key="k_s1")
            sp1 = st.slider("Espacement des lignes :", 1.2, 3.0, 2.0, 0.1, key="k_sp1")
        st.write("### 👁️ Aperçu adapté :")
        render_dys_text(txt, m1, s1, sp1)

with tab2:
    st.write("### Importer une image pour extraction et adaptation")
    file = st.file_uploader("Choisissez une image (PNG, JPG)", type=["png", "jpg", "jpeg"])
    if file:
        img = Image.open(file)
        st.image(img, caption="Image importée", use_container_width=True)
        try:
            ext_txt = pytesseract.image_to_string(img, lang="fra")
            if ext_txt.strip():
                st.success("Texte extrait avec succès !")
                
                with st.expander("Voir / Modifier le texte brut extrait"):
                    ext_txt = st.text_area("Texte détecté :", ext_txt, height=140, key="editable_ocr")
                
                st.write("---")
                st.write("### ⚙️ Options de mise en page DYS & Phonétique")
                c1, c2 = st.columns(2)
                with c1:
                    m2 = st.selectbox("Option pédagogique :", opts, key="k_m2")
                with c2:
                    s2 = st.slider("Taille de police (px) :", 14, 32, 22, key="k_s2")
                    sp2 = st.slider("Espacement des lignes :", 1.2, 3.0, 2.0, 0.1, key="k_sp2")
                st.write("### 👁️ Aperçu adapté :")
                render_dys_text(ext_txt, m2, s2, sp2)
            else:
                st.warning("Aucun texte lisible n'a été trouvé dans cette image.")
        except Exception as e:
            st.error(f"Erreur lors de la lecture de l'image : {e}")

st.write("---")
st.caption("Ophélie Bascou Drimaracci - Application Pédagogique DYS")
