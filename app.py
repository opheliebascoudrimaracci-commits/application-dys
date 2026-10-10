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

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

# Dictionnaire exact basé sur votre image de référence des sons complexes
EXACT_COMPLEX_SOUNDS = {
    # Marron (ON)
    'on': ('#8B4513', 'ɔ̃'),
    # Brun (UN)
    'un': ('#A0522D', 'œ̃'),
    # Rouge (OU)
    'ou': ('#FF0000', 'u'),
    # Orange (AN, EN)
    'an': ('#FF8C00', 'ɑ̃'),
    'en': ('#FF8C00', 'ɑ̃'),
    # Jaune (O, AU, EAU)
    'eau': ('#FFD700', 'o'),
    'au': ('#FFD700', 'o'),
    'o': ('#FFD700', 'o'),
    # Violet (ET, EZ, ER, AI, EI)
    'et': ('#800080', 'e'),
    'ez': ('#800080', 'e'),
    'er': ('#800080', 'e'),
    'ai': ('#800080', 'ɛ'),
    'ei': ('#800080', 'ɛ'),
    # Bleu (EU, OEU)
    'oeu': ('#0000FF', 'ø'),
    'eu': ('#0000FF', 'ø'),
    # Vert Sapin (IN, AIN, EIN)
    'ain': ('#1E4D2B', 'ɛ̃'),
    'ein': ('#1E4D2B', 'ɛ̃'),
    'in': ('#1E4D2B', 'ɛ̃'),
    # Jaune / Doré (CH)
    'ch': ('#DAA520', 'ʃ'),
    # Autres sons fréquents
    'oi': ('#e74c3c', 'wa'),
    'oin': ('#d35400', 'waɛ̃'),
    'ien': ('#e67e22', 'jɛ̃'),
    'ph': ('#8e44ad', 'f'),
    'gn': ('#16a085', 'ɲ')
}

def is_muted_letter(word, index):
    """Détermine si une lettre est muette (ex: e final, s/t/d/x finaux)."""
    w_lower = word.lower()
    length = len(w_lower)
    
    # 'e' final (pour les mots de plus de 2 lettres)
    if w_lower[index] == 'e' and index == length - 1 and length > 2:
        return True
    # Consonnes finales muettes courantes
    if index == length - 1 and w_lower[index] in ['s', 't', 'd', 'x', 'z']:
        if w_lower not in ['bus', 'gaz', 'riz', 'six', 'dix']:
            return True
            
    return False

def count_syllables(word):
    """Calcule le nombre de syllabes d'un mot."""
    w = word.strip()
    if len(w) <= 3:
        return 1
    matches = list(re.finditer(r'[^aeiouyàâéèêëîïôûùü]*[aeiouyàâéèêëîïôûùü]+(?:[^aeiouyàâéèêëîïôûùü](?![aeiouyàâéèêëîïôûùü]))?', w, re.IGNORECASE))
    return max(1, len(matches))

def parse_word_to_blocks(word):
    """Découpe un mot en blocs : sons complexes colorés, lettres muettes grisées ou lettres neutres."""
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
            muted = is_muted_letter(word, i)
            blocks.append({
                'text': char,
                'color': '',
                'phoneme': '',
                'is_complex': False,
                'is_muted': muted
            })
            i += 1
    return blocks

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes):
    blocks = parse_word_to_blocks(word)
    
    # 1. Étage Texte principal (sons complexes colorés, lettres muettes en gris)
    text_html = ""
    for b in blocks:
        if b['is_muted']:
