import streamlit as st
import pytesseract
from PIL import Image

# 1. Configuration unique de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci",
    page_icon="✏️",
    layout="wide"
)

# 2. Injection CSS pour forcer le fond blanc et le texte en noir
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Ophélie Bascou Drimaracci",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

   # Dictionnaire des sons complexes
EXACT_COMPLEX_SOUNDS = {
    # Marron (ON)
    'on': ('#8B4513', 'on'),
    # Brun (UN)
    'un': ('#A0522D', 'un'),
    # Rouge (OU)
    'ou': ('#FF0000', 'ou'),
    # Orange (AN, EN)
    'an': ('#FF8C00', 'an'),
    'en': ('#FF8C00', 'an'),
    # Jaune (O, AU, EAU)
    'eau': ('#FFD700', 'o'),
    'au': ('#FFD700', 'o'),
    'o': ('#FFD700', 'o'),
    # Violet (ET, EZ, ER, AI, EI, ESS, ERR, ELL, EFF, ETT)
    'et': ('#800080', 'é'),
    'é': ('#800080', 'é'),
    'ez': ('#800080', 'é'),
    'er': ('#800080', 'é'),
    'ai': ('#800080', 'è'),
    'ei': ('#800080', 'è'),
    'esse': ('#800080', 'é'),
    'erre'': ('#800080', 'é'),
    'elle': ('#800080', 'é'),
    'effe': ('#800080', 'é'),
    'ette': ('#800080', 'é'),
    # Bleu (EU, OEU)
    'oeu': ('#0000FF', 'eu'),
    'eu': ('#0000FF', 'eu'),
    # Vert Sapin (IN, AIN, EIN)
    'ain': ('#1E4D2B', 'in'),
    'ein': ('#1E4D2B', 'in'),
    'in': ('#1E4D2B', 'in'),
    # Jaune / Doré (CH)
    'ch': ('#DAA520', 'ch'),
    # Autres sons fréquents
    'oi': ('#e74c3c', 'oi'),
    'oin': ('#d35400', 'oin'),
    'ien': ('#e67e22', 'ien'),
    'ph': ('#8e44ad', 'f'),
    'gn': ('#16a085', 'gn'),
    # Autres sons fréquents et graphies complexes
    'qu': ('#8e44ad', 'k'),   # Le "qu" qui fait "k"
    'ph': ('#8e44ad', 'f'),   # Le "ph" qui fait "f"
    'gn': ('#16a085', 'gn'),
    'oi': ('#e74c3c', 'oi'),
    'oin': ('#d35400', 'oin'),
    'ien': ('#e67e22', 'ien'),
}
def is_muted_letter(word, index):
    """Détermine si une lettre est muette (ex: e final, s/t/d/x finaux)."""
    w_lower = word.lower()
    length = len(w_lower)
    
    # Ne jamais griser le 'e' final si le mot se termine par une double consonne + e (ex: appelle, terre, tasse)
    if index == length - 1 and w_lower[index] == 'e' and length > 2:
        if re.search(r'([b-df-hj-np-tv-z])\1e$', w_lower):
            return False
        return True

    # Consonnes finales muettes courantes
    if index == length - 1 and w_lower[index] in ['s', 't', 'd', 'x', 'z']:
        if w_lower not in ['bus', 'gaz', 'riz', 'six', 'dix']:
            return True
            
    return False

from phonemizer import phonemize
import re
def count_syllables(word):
    word = word.strip()

    if not word:
        return 0

    phonemes = phonemize(
        word,
        language="fr-fr",
        backend="espeak",
        strip=True,
        preserve_punctuation=False,
        with_stress=False
    )

    # Compte les noyaux vocaliques dans la transcription phonétique.
    vowels = re.findall(
        r"[iyɪeɛæaɑɒɔoʊuʌəœøɐɜɞɤɯ]",
        phonemes
    )

    return len(vowels)


def split_into_syllables_spans(word):
    """Découpe approximativement un mot en tranches."""
    w = word.strip().lower()

    if not w:
        return []

    if len(w) <= 3:
        return [(0, len(w))]

    pattern = r'[^aeiouyàâéèêëîïôûùü]*[aeiouyàâéèêëîïôûùü]+(?:[^aeiouyàâéèêëîïôûùü](?![aeiouyàâéèêëîïôûùü]))?'

    matches = list(re.finditer(pattern, w))

    if not matches:
        return [(0, len(w))]

    spans = [(m.start(), m.end()) for m in matches]

    if spans[-1][1] < len(w):
        spans[-1] = (spans[-1][0], len(w))

    return spans

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes):
    blocks = parse_word_to_blocks(word)
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block['text']
        r_type = block.get('render_type', 'normal')
        
        # 1. Lettres muettes (gris clair doux)
        if r_type == 'muted':
            part_html = f"<span style='color: #b0b0b0; opacity: 0.5;'>{text}</span>"
            
        # 2. Sons complexes -> Surlignage de fond pastel
        elif r_type == 'highlight' and show_colors and block.get('color'):
            bg_color = block['color'] + '33' 
            part_html = f"<span style='background-color: {bg_color}; padding: 2px 4px; border-radius: 4px; font-weight: bold;'>{text}</span>"
            
        # 3. Lettres contextuelles -> Changement de couleur de la lettre
        elif r_type == 'color_text' and show_colors and block.get('color'):
            part_html = f"<span style='color: {block['color']}; font-weight: bold;'>{text}</span>"
            
        # 4. Lettres normales
        else:
            part_html = text
            
        word_html_parts.append(part_html)
        
        # Phonèmes en dessous
        if show_phonemes and block.get('phoneme'):
            ph_color = block.get('color') if (block.get('color') and show_colors) else '#000000'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-weight: bold;'>[{block['phoneme']}]</span>")
        else:
            phoneme_html_parts.append("<span style='visibility: hidden;'>•</span>")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""


    return html

def split_into_syllables_spans(word):
    """Découpe un mot en tranches (gardé au cas où)."""
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

# Dictionnaire de couleurs unifié
PHONEME_COLORS = {
    'ou': '#ff6b6b',  # Rouge pastel (surlignage)
    'on': '#f08c00',  # Orange pastel (surlignage)
    'è': '#cc5de8',   # Violet pastel (surlignage)
    'é': '#cc5de8',   # Violet pastel (surlignage)
    'k': '#2563eb',   # Bleu (couleur de la lettre c)
    's': '#059669',   # Vert (couleur de la lettre c)
    'z': '#0d9488'    # Turquoise (couleur de la lettre s entre deux voyelles)
}

def parse_word_to_blocks(word):
    blocks = []
    w_lower = word.lower()
    
    # 1. Mots entiers spécifiques
    if w_lower == "est":
        return [{
            'text': word,
            'is_muted': False,
            'render_type': 'highlight',
            'color': PHONEME_COLORS['è'],
            'phoneme': 'è'
        }]
    
    if w_lower == "c'est":
        return [
            {'text': 'c', 'is_muted': False, 'render_type': 'color_text', 'color': PHONEME_COLORS['k'], 'phoneme': 'k'},
            {'text': "'", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': 'est', 'is_muted': False, 'render_type': 'highlight', 'color': PHONEME_COLORS['è'], 'phoneme': 'è'}
        ]

    i = 0
    n = len(word)
    while i < n:
        char = word[i]
        c_lower = char.lower()
        
        # --- 'h' muet (Mathis, Théâtre) ---
        if c_lower == 'h':
            if i == 0 or word[i-1].lower() not in ['c', 'p']:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
                i += 1
                continue

        # --- Sons complexes (ou, on) -> Surlignage de fond ---
        if w_lower[i:i+2] == 'ou':
            blocks.append({'text': word[i:i+2], 'is_muted': False, 'render_type': 'highlight', 'color': PHONEME_COLORS['ou'], 'phoneme': 'ou'})
            i += 2
            continue
        elif w_lower[i:i+2] == 'on':
            blocks.append({'text': word[i:i+2], 'is_muted': False, 'render_type': 'highlight', 'color': PHONEME_COLORS['on'], 'phoneme': 'on'})
            i += 2
            continue

        # --- Consonnes doubles ---
        if i + 1 < n and c_lower in ['p', 't', 'm', 'n', 'l', 'b', 'd', 'f', 'r', 's'] and word[i+1].lower() == c_lower:
            blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue

        # --- Le 'e' avant double consonne (ex: appelle -> [è]) -> Surlignage de fond ---
        if c_lower == 'e':
            is_before_double = (i + 2 < n and word[i+1].lower() == word[i+2].lower())
            is_final_mute = (i == n - 1 and n > 2)
            
            if is_before_double:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'highlight', 'color': PHONEME_COLORS['è'], 'phoneme': 'è'})
                i += 1
                continue
            elif is_final_mute:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
                i += 1
                continue

        # --- Règles contextuelles (C) -> Changement de couleur de la LETTRE ---
        if c_lower == 'c':
            next_char = word[i+1].lower() if i + 1 < n else ''
            if next_char in ['e', 'i', 'y']:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': PHONEME_COLORS['s'], 'phoneme': 's'})
            elif next_char not in ['h', '']:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': PHONEME_COLORS['k'], 'phoneme': 'k'})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue
            
        # --- Règles contextuelles (S) -> Changement de couleur de la LETTRE (ex: entre deux voyelles) ---
        if c_lower == 's':
            is_prev_vowel = (i > 0 and word[i-1].lower() in 'aeiouyàâéèêëîïôûù')
            is_next_vowel = (i + 1 < n and word[i+1].lower() in 'aeiouyàâéèêëîïôûù')
            is_final = (i == n - 1)
            
            if is_prev_vowel and is_next_vowel:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': PHONEME_COLORS['z'], 'phoneme': 'z'})
            elif is_final:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue

        # Fin de mot muette générale
        if i == n - 1 and c_lower in ['t', 'd', 'x'] and n > 2:
            blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 1
            continue

        # Par défaut : caractère standard
        blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
        i += 1
        
    return blocks

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes):
    blocks = parse_word_to_blocks(word)
    word_html_parts = []
    phoneme_html_parts = []
    arc_html_parts = []
    
    for block in blocks:
        text = block['text']
        r_type = block.get('render_type', 'normal')
        
        # 1. Lettres muettes (gris clair doux)
        if r_type == 'muted':
            part_html = f"<span style='color: #b0b0b0; opacity: 0.5;'>{text}</span>"
            
        # 2. Sons complexes -> Surlignage de fond pastel
        elif r_type == 'highlight' and show_colors and block.get('color'):
            bg_color = block['color'] + '33' 
            part_html = f"<span style='background-color: {bg_color}; padding: 2px 4px; border-radius: 4px; font-weight: bold;'>{text}</span>"
            
        # 3. Lettres contextuelles -> Changement de couleur de la lettre
        elif r_type == 'color_text' and show_colors and block.get('color'):
            part_html = f"<span style='color: {block['color']}; font-weight: bold;'>{text}</span>"
            
        # 4. Lettres normales
        else:
            part_html = text
            
        word_html_parts.append(part_html)
        
        # Phonèmes en dessous
        if show_phonemes and block.get('phoneme'):
            ph_color = block.get('color') if (block.get('color') and show_colors) else '#000000'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-weight: bold;'>[{block['phoneme']}]</span>")
        else:
            phoneme_html_parts.append("<span style='visibility: hidden;'>•</span>")
            
        # Arcs / points : un seul point par bloc non muet (pour correspondre au rythme des sons/syllabes)
        if show_arcs:
            if not block.get('is_muted', False):
                arc_html_parts.append("•")
            else:
                arc_html_parts.append(" ") # Pas de point pour les lettres muettes
        else:
            arc_html_parts.append(" ")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""
    w_arcs = " ".join(arc_html_parts) if show_arcs else ""
    
    html = f"<span style='display: inline-block; text-align: center; margin-right: 20px;'>"
    html += f"<div>{w_main}</div>"
    if show_arcs:
        html += f"<div style='font-size: 0.9em; color: #4a90e2; letter-spacing: 2px; margin-top: 2px;'>{w_arcs}</div>"
    if show_phonemes:
        html += f"<div style='font-size: 0.75em; margin-top: 2px;'>{w_ph}</div>"
    html += f"</span>"
    
    return html
    
def render_full_dys_text(text, show_colors, show_arcs, show_phonemes, word_alt, line_alt, soft_bg, size, spacing):
    if not text:
        return
        
    lines = text.split('\n')
    rendered_lines = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words = []
        
        for word_idx, word in enumerate(words):
            word_html = render_word_multilevel(word, show_colors, show_arcs, show_phonemes)
            
            if word_alt and not show_colors:
                color = "#0055ff" if word_idx % 2 == 0 else "#cc0000"
                word_html = f"<span style='color: {color}; font-weight: bold;'>{word_html}</span>"
                
            rendered_words.append(word_html)
            
        line_content = " ".join(rendered_words)
        
        if line_alt and not show_colors:
            line_color = "#0055ff" if line_idx % 2 == 0 else "#cc0000"
            line_content = f"<div style='color: {line_color};'>{line_content}</div>"
            
        rendered_lines.append(line_content)
        
    full_content = "<br><br>".join(rendered_lines)
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2; color: #111111;" if soft_bg else ""
    
    html_output = f"<div style='font-size: {size}px; line-height: {spacing}; {style_bg}'>{full_content}</div>"
    st.markdown(html_output, unsafe_allow_html=True)

def build_controls(key_prefix):
    st.write("### 🎛️ Options d'adaptation DYS (Cumulables)")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("**Aides aux sons & syllabes :**")
        show_colors = st.checkbox("Colorer selon votre code couleur de référence", value=True, key=f"{key_prefix}_colors")
        show_arcs = st.checkbox("Afficher les ponts syllabiques", value=True, key=f"{key_prefix}_arcs")
        show_phonemes = st.checkbox("Écrire les sons/phonèmes en dessous", value=True, key=f"{key_prefix}_phonemes")
        
    with c2:
        st.write("**Aides à la ligne & visuel :**")
        word_alt = st.checkbox("Alternance des mots (Bleu/Rouge)", value=False, key=f"{key_prefix}_walt")
        line_alt = st.checkbox("Alternance des lignes", value=False, key=f"{key_prefix}_lalt")
        soft_bg = st.checkbox("Surlignage doux du fond", value=False, key=f"{key_prefix}_bg")
        
    with c3:
        st.write("**Typographie :**")
        size = st.slider("Taille de police (px) :", 16, 36, 24, key=f"{key_prefix}_size")
        spacing = st.slider("Espacement des lignes :", 1.5, 4.0, 2.5, 0.1, key=f"{key_prefix}_space")
        
    return {
        "show_colors": show_colors,
        "show_arcs": show_arcs,
        "show_phonemes": show_phonemes,
        "word_alt": word_alt,
        "line_alt": line_alt,
        "soft_bg": soft_bg,
        "size": size,
        "spacing": spacing
    }
# ONGLET 1
with tab1:
    st.write("### Saisir ou coller un texte")
    txt = st.text_area("Entrez votre texte ici :", height=140, placeholder="Tapez ou collez votre texte...")
    if txt:
        st.write("---")
        opts = build_controls("t1")
        render_full_dys_text(txt, **opts)
# ONGLET 2
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
                with st.expander("Voir / Modifier le texte extrait"):
                    ext_txt = st.text_area("Texte détecté :", ext_txt, height=120, key="ocr_edit")
                st.write("---")
                opts2 = build_controls("t2")
                st.write("### 👁️ Aperçu adapté :")
                render_full_dys_text(ext_txt, *opts2)
            else:
                st.warning("Aucun texte trouvé dans l'image.")
        except Exception as e:
            st.error(f"Erreur d'extraction OCR : {e}")

st.write("---")
st.caption("Ophélie Bascou Drimaracci - Application Pédagogique DYS")
