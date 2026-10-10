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
def count_syllables(word):
    """Calcule le nombre de syllabes d'un mot."""
    w = word.strip()
    if len(w) <= 3:
        return 1
    matches = list(re.finditer(r'[^aeiouyàâéèêëîïôûùü]*[aeiouyàâéèêëîïôûùü]+(?:[^aeiouyàâéèêëîïôûùü](?![aeiouyàâéèêëîïôûùü]))?', w, re.IGNORECASE))
    return max(1, len(matches))

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

def parse_word_to_blocks(word):
    """Découpe un mot en blocs avec gestion prioritaire des sons contextuels et complexes."""
    blocks = []
    i = 0
    w_lower = word.lower()
    voyelles = "aeiouyàâéèêëîïôûùü"
    
    while i < len(word):
        matched = False
        char = w_lower[i]
        next_char = w_lower[i+1] if i + 1 < len(w_lower) else ''
        
        # --- 1. RÈGLE : Double consonne + 'e' (ex: lle, rre, sse...) -> Son [é] ---
        double_match = re.match(r'^([b-df-hj-np-tv-z])\1e', w_lower[i:])
        if double_match:
            matched_str = word[i:i+3]
            blocks.append({
                'text': matched_str,
                'color': '#800080',  # Violet pour le son [é]
                'phoneme': 'é',
                'is_complex': True,
                'is_muted': False
            })
            i += 3
            matched = True
            continue

        # --- 2. LE C CONTEXTUEL (ex: case -> [k], cerise -> [s]) ---
        if char == 'c':
            if next_char in ['e', 'i', 'y', 'é', 'è']:
                phoneme = 's'
            else:
                phoneme = 'k'
            blocks.append({
                'text': word[i],
                'color': '',       # Pas de couleur spéciale sur la lettre elle-même
                'phoneme': phoneme, # Affiche [k] ou [s] en dessous
                'is_complex': True,
                'is_muted': False
            })
            i += 1
            matched = True
            continue
            
        # --- 3. LE S INTERVOCALIQUE (entre deux voyelles -> [z]) ---
        elif char == 's':
            est_entre_voyelles = (i > 0 and i < len(word) - 1 and w_lower[i-1] in voyelles and next_char in voyelles)
            if est_entre_voyelles:
                blocks.append({
                    'text': word[i],
                    'color': '',
                    'phoneme': 'z',  # Affiche [z] en dessous
                    'is_complex': True,
                    'is_muted': False
                })
                i += 1
                matched = True
                continue

        # --- 4. SONS COMPLEXES DU DICTIONNAIRE (ex: ou, on, in, qu...) ---
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
                
        if matched:
            continue

        # --- 5. LETTRE CLASSIQUE OU MUETTE ---
        muted = is_muted_letter(word, i)
        blocks.append({
            'text': word[i],
            'color': '',
            'phoneme': '',
            'is_complex': False,
            'is_muted': muted
        })
        i += 1
        
    return blocks

def render_word_multilevel(word, show_colors=True, show_arcs=True, show_phonemes=True):
    blocks = parse_word_to_blocks(word)
    
    # 1. Étage Texte principal
    text_html = ""
    for b in blocks:
        if b['is_muted']:
            text_html += f"<span style='color: #b0b0b0; opacity: 0.6;'>{b['text']}</span>"
        elif show_colors and b['color']:
            text_html += f"<span style='color: {b['color']}; font-weight: bold;'>{b['text']}</span>"
        else:
            text_html += f"<span>{b['text']}</span>"
            
    # 2. Étage Points de syllabes
    dots_html = ""
    if show_arcs:
        nb_syllables = count_syllables(word)
        dots = " &nbsp; ".join(["•"] * nb_syllables)
        dots_html = f"<span style='color: #4a90e2; font-size: 1.2em; font-weight: bold;'>{dots}</span>"

    # 3. Étage Sons simples (phonèmes)
    phonemes_html = ""
    if show_phonemes:
        p_list = []
        for b in blocks:
            if b['is_muted']:
                p_list.append("&nbsp;" * len(b['text']))
            elif b['is_complex'] and b['phoneme']:
                c = b['color'] if (show_colors and b['color']) else '#888888'
                p_list.append(f"<span style='color: {c}; font-size: 0.75em; font-weight: bold;'>[{b['phoneme']}]</span>")
            else:
                p_list.append("&nbsp;" * len(b['text']))
        phonemes_html = "".join(p_list)

    # Assemblage final de la carte du mot
    res = f"<div style='display: inline-flex; flex-direction: column; align-items: center; margin: 0 8px; vertical-align: top;'>"
    res += f"<div style='letter-spacing: 1px;'>{text_html}</div>"
    if show_arcs:
        res += f"<div style='margin-top: 2px; height: 18px; display: flex; align-items: center;'>{dots_html}</div>"
    if show_phonemes:
        res += f"<div style='margin-top: 2px; letter-spacing: 2px;'>{phonemes_html}</div>"
    res += "</div>"
    
    return res

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

def build_controls(key_prefix="main"):
    st.sidebar.subheader("Paramètres d'affichage")
    show_colors = st.sidebar.checkbox("Afficher les couleurs", value=True, key=f"{key_prefix}_colors")
    show_arcs = st.sidebar.checkbox("Afficher les points de syllabes", value=True, key=f"{key_prefix}_arcs")
    show_phonemes = st.sidebar.checkbox("Écrire les sons/phonèmes en dessous", value=True, key=f"{key_prefix}_phonemes")
    
    return {
        "show_colors": show_colors,
        "show_arcs": show_arcs,
        "show_phonemes": show_phonemes
    }
# ONGLET 1
with tab1:
    st.write("### Saisir ou coller un texte")
    txt = st.text_area("Entrez votre texte ici :", height=140, placeholder="Tapez ou collez votre texte...")
    if txt:
        st.write("---")
        opts = build_controls("t1")
        st.write("### 👁️ Aperçu adapté :")
        render_full_dys_text(txt, *opts)

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
