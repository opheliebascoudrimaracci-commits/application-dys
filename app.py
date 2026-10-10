import streamlit as st
import pytesseract
from PIL import Image
import re

st.set_page_config(
    page_title="Ophélie Bascou Drimaracci - Outils Pédagogiques DYS",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

# --- BARRE LATÉRALE : OPTIONS TOUJOURS ACCESSIBLES ---
st.sidebar.header("⚙️ Options d'adaptation DYS")

show_colors = st.sidebar.checkbox("Colorer les sons complexes", value=True)
show_arcs = st.sidebar.checkbox("Afficher les ponts syllabiques", value=True)
show_phonemes = st.sidebar.checkbox("Écrire les sons/phonèmes en dessous", value=True)

st.sidebar.markdown("---")
word_alt = st.sidebar.checkbox("Alternance des mots (Bleu/Rouge)", value=False)
line_alt = st.sidebar.checkbox("Alternance des lignes", value=False)
soft_bg = st.sidebar.checkbox("Surlignage doux du fond", value=False)

st.sidebar.markdown("---")
size = st.sidebar.slider("Taille de police (px) :", 16, 36, 24)
spacing = st.sidebar.slider("Espacement des lignes :", 1.5, 4.0, 2.5, 0.1)

# --- DICTIONNAIRE DES SONS COMPLEXES ---
EXACT_COMPLEX_SOUNDS = {
    'on': ('#8B4513', 'ɔ̃'),
    'un': ('#A0522D', 'œ̃'),
    'ou': ('#FF0000', 'u'),
    'an': ('#FF8C00', 'ɑ̃'),
    'en': ('#FF8C00', 'ɑ̃'),
    'eau': ('#FFD700', 'o'),
    'au': ('#FFD700', 'o'),
    'o': ('#FFD700', 'o'),
    'et': ('#800080', 'e'),
    'ez': ('#800080', 'e'),
    'er': ('#800080', 'e'),
    'ai': ('#800080', 'ɛ'),
    'ei': ('#800080', 'ɛ'),
    'oeu': ('#0000FF', 'ø'),
    'eu': ('#0000FF', 'ø'),
    'ain': ('#1E4D2B', 'ɛ̃'),
    'ein': ('#1E4D2B', 'ɛ̃'),
    'in': ('#1E4D2B', 'ɛ̃'),
    'ch': ('#DAA520', 'ʃ'),
    'oi': ('#e74c3c', 'wa'),
    'oin': ('#d35400', 'waɛ̃'),
    'ien': ('#e67e22', 'jɛ̃'),
    'ph': ('#8e44ad', 'f'),
    'gn': ('#16a085', 'ɲ')
}

def is_muted_letter(word, index):
    w_lower = word.lower()
    length = len(w_lower)
    if w_lower[index] == 'e' and index == length - 1 and length > 2:
        return True
    if index == length - 1 and w_lower[index] in ['s', 't', 'd', 'x', 'z']:
        if w_lower not in ['bus', 'gaz', 'riz', 'six', 'dix']:
            return True
    return False

def split_into_syllables_spans(word):
    w = word.strip()
    if len(w) <= 3:
        return [(0, len(w))]
    matches = list(re.finditer(r'[^aeiouyàâéèêëîïôûùü]*[aeiouyàâéèêëîïôûùü]+(?:[^aeiouyàâéèêëîïôûùü](?![aeiouyàâéèêëîïôûùü]))?', w, re.IGNORECASE))
    if not matches:
        return [(0, len(w))]
    spans = [(m.start(), m.end()) for m in matches]
    if spans[-1][1] < len(w):
        spans[-1] = (spans[-1][0], len(w))
    return spans

def parse_word_to_blocks(word):
    blocks = []
    i = 0
    w_lower = word.lower()
    while i < len(word):
        matched = False
        for sound in sorted(EXACT_COMPLEX_SOUNDS.keys(), key=len, reverse=True):
            if w_lower[i:].startswith(sound):
                color, phoneme = EXACT_COMPLEX_SOUNDS[sound]
                blocks.append({
                    'text': word[i:i+len(sound)],
                    'color': color,
                    'phoneme': phoneme,
                    'is_complex': True,
                    'is_muted': False
                })
                i += len(sound)
                matched = True
                break
        if not matched:
            char = word[i]
            
