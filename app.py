import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image
import re
import unicodedata

# 1. Configuration unique de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci",
    page_icon="✏️",
    layout="wide"
)

# 2. Injection CSS avec la police OpenDyslexic (depuis Google Fonts)
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap" rel="stylesheet">
    <style>
    .stApp, html, body, [class*="css"] {
        font-family: 'Open Dyslexic', sans-serif !important;
        background-color: #FFFFFF !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #000000 !important;
        font-family: 'Open Dyslexic', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

# Dictionnaire des sons complexes
EXACT_COMPLEX_SOUNDS = {
    'eau': ('#FFD700', 'o'),
    'au': ('#FFD700', 'o'),
    'oeu': ('#0000FF', 'eu'),
    'eu': ('#0000FF', 'eu'),
    'ain': ('#1E4D2B', 'in'),
    'ein': ('#1E4D2B', 'in'),
    'in': ('#1E4D2B', 'in'),
    'on': ('#8B4513', 'on'),
    'un': ('#A0522D', 'un'),
    'ou': ('#FF0000', 'ou'),
    'an': ('#FF8C00', 'an'),
    'en': ('#FF8C00', 'en'),
    'et': ('#800080', 'é'),
    'ez': ('#800080', 'é'),
    'er': ('#800080', 'é'),
    'ai': ('#800080', 'è'),
    'ei': ('#800080', 'è'),
    'ch': ('#DAA520', 'ch'),
    'oi': ('#000000', 'oi'),
    'oin': ('#d35400', 'oin'),
    'ien': ('#e67e22', 'ien'),
    'ph': ('#8e44ad', 'f'),
    'gn': ('#16a085', 'gn'),
    'qu': ('#8e44ad', 'k'),
    'o': ('#FFD700', 'o'),
    'é': ('#800080', 'é'),
}

VOWELS = "aeiouyàâäéèêëïîôöùûüÿ"

def count_syllables(word):
    """Estimation des syllabes françaises par règles et exceptions."""
    w = word.strip().lower().strip(".,;:!?()[]{}\"'«»")
    if not w:
        return 0

    exceptions = {
        "bonjour": 2, "napoléon": 4, "comment": 2, "mathis": 2, "théâtre": 2,
        "dans": 1, "une": 1, "tu": 1, "vas": 1, "je": 1, "m'appelle": 2,
        "aujourd'hui": 3, "oiseau": 2, "beaucoup": 2, "famille": 2, "fille": 1,
        "maison": 2, "cheval": 2, "bateau": 2, "ordinateur": 4, "magnifique": 3,
    }

    if w in exceptions:
        return exceptions[w]

    if "'" in w or "’" in w:
        parts = re.split(r"['’]", w)
        return sum(count_syllables(p) for p in parts if p)

    w = w.replace("-", "")

    pattern = (
        r"eau|oeu|œu|"
        r"ain|aim|ein|"
        r"oi|ou|au|eu|ai|ei|"
        r"an|am|en|em|on|om|in|im|un|um|"
        r"[aeiouyàâäéèêëïîôöùûüÿ]"
    )

    count = len(re.findall(pattern, w))

    if w.endswith("e") and not w.endswith(("ée", "ie", "ue", "eau")):
        count -= 1

    if w.endswith("es") and len(w) > 3:
        count -= 1
    elif w.endswith("ent") and len(w) > 4:
        count -= 1

    return max(1, count)

count_syllables_approx = count_syllables

def parse_word_to_blocks(word):
    blocks = []
    w_lower = word.lower()
    
    if w_lower == "est":
        color, ph = EXACT_COMPLEX_SOUNDS.get('et', ('#800080', 'è'))
        return [{'text': word, 'is_muted': False, 'render_type': 'highlight', 'color': color, 'phoneme': ph}]
    
    if w_lower == "c'est":
        return [
            {'text': 'c', 'is_muted': False, 'render_type': 'color_text', 'color': '#2563eb', 'phoneme': 'k'},
            {'text': "'", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': 'est', 'is_muted': False, 'render_type': 'highlight', 'color': '#800080', 'phoneme': 'è'}
        ]

    i = 0
    n = len(word)
    sorted_keys = sorted(EXACT_COMPLEX_SOUNDS.keys(), key=len, reverse=True)
    
    while i < n:
        char = word[i]
        c_lower = char.lower()
        
        if c_lower == 'h':
            if i == 0 or word[i-1].lower() not in ['c', 'p']:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
                i += 1
                continue

        matched_complex = False
        for key in sorted_keys:
            if w_lower[i:i+len(key)] == key:
                color, phoneme = EXACT_COMPLEX_SOUNDS[key]
                blocks.append({
                    'text': word[i:i+len(key)],
                    'is_muted': False,
                    'render_type': '
