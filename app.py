import streamlit as st
import pytesseract
from PIL import Image
import re

st.set_page_config(page_title="Outils DYS", page_icon="✏️", layout="wide")

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
        
    st.markdown(f"<div style='{style}'>{content}</div>
