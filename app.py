import streamlit as st
import pytesseract
from PIL import Image
import re

# Configuration de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci - Outils Pédagogiques",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

# Navigation par onglets
tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

# --- Fonctions d'adaptation DYS et Phonétique ---

def colorize_phonemes(word):
    """Colorie les graphèmes/sons spécifiques (voyelles et sons complexes)"""
    vowels = {'a': '#cc0000', 'e': '#0055ff', 'i': '#00aa00', 'o': '#ff6600', 'u': '#9900cc', 'y': '#00aa00'}
    result = ""
    i = 0
    while i < len(word):
        # Gestion de quelques sons complexes fréquents en français
        if i < len(word) - 1 and word[i:i+2].lower() in ['ou', 'an', 'en', 'in', 'on', 'un', 'ch', 'ph', 'gn', 'ei', 'ai', 'au', 'eu']:
            son = word[i:i+2]
            result += f"<span style='color: #e67e22; font-weight: bold;'>{son}</span>"
            i += 2
        elif word[i].lower() in vowels:
            v = word[i]
            color = vowels[v.lower()]
            result += f"<span style='color: {color}; font-weight: bold;'>{v}</span>"
            i += 1
        else:
            result += word[i]
            i += 1
    return result

def get_syllables_with_arcs(word):
    """Découpe approximativement en syllabes et ajoute des ponts sous les syllabes"""
    # Règle simple de césure visuelle pour l'exemple pédagogique
    word_lower = word.lower()
    # Si le mot est court, on le laisse tel quel
    if len(word) <= 3:
        return f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{word}</span>"
    
    # Découpage basique autour des consonnes suivies de voyelles
    parts = re.findall(r'.{1,2}(?=[aeiouy]|$)', word)
    if len(parts) > 1:
        syllables_html = " ‿ ".join([f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{p}</span>" for p in parts])
        return syllables_html
    else:
        return f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{word}</span>"

def render_dys_text(text, color_mode, font_size, line_spacing):
    if not text:
        return
    
    style = f"font-size: {font_size}px; line-height: {line_spacing};"
    
    if color_mode == "Coloration des sons (Phonèmes)":
        words = text.split()
        colored_words = [colorize_phonemes(w) for w in words]
        content = ' '.join(colored_words)
        
    elif color_mode == "Ponts et découpage syllabique":
        words = text.split()
        syllable_words = [get_syllables_with_arcs(w) for w in words]
        content = ' '.join(syllable_words)
        
    elif color_mode == "Alternance des mots (Bleu / Rouge)":
        words = text.
