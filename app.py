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

VOWELS = {
    'a': ('#cc0000', 'a'),
    'e': ('#0055ff', 'ə'),
    'i': ('#00aa00', 'i'),
    'u': ('#9900cc', 'y'),
    'y': ('#00aa00', 'i')
}

def parse_word_to_blocks(word):
    """Découpe un mot en blocs selon votre code couleur de référence."""
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
                    'is_complex': True
                })
                i += len(sound)
                matched = True
                break
        if not matched:
            char = word[i]
            c_lower = char.lower()
            if c_lower in VOWELS:
                color, phoneme = VOWELS[c_lower]
                blocks.append({
                    'text': char,
                    'color': color,
                    'phoneme': phoneme,
                    'is_complex': False
                })
            else:
                blocks.append({
                    'text': char,
                    'color': '#333333',
                    'phoneme': '',
                    'is_complex': False
                })
            i += 1
    return blocks

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes):
    blocks = parse_word_to_blocks(word)
    
    # 1. Étage Texte
    text_html = ""
    for b in blocks:
        if show_colors and b['color'] != '#333333':
            text_html += f"<span style='color: {b['color']}; font-weight: bold;'>{b['text']}</span>"
        else:
            text_html += f"<span>{b['text']}</span>"
            
    # 2. Étage Ponts syllabiques
    parts = re.findall(r'.{1,2}(?=[aeiouyàâéèêëîïôûùü]|$)', word, flags=re.IGNORECASE) or [word]
    arcs_html = " ‿ ".join([f"<span style='border-bottom: 2px solid #4a90e2; padding-bottom: 2px;'>{p}</span>" for p in parts]) if show_arcs else ""
    
    # 3. Étage Phonèmes
    phonemes_html = ""
    if show_phonemes:
        p_list = [f"<span style='color: {b['color'] if show_colors else '#666'}; font-size: 0.7em;'>[{b['phoneme']}]</span>" if b['phoneme'] else "&nbsp;" for b in blocks]
        phonemes_html = "".join(p_list)

    res = f"<div style='display: inline-flex; flex-direction: column; align-items: center; margin: 0 4px; vertical-align: top;'>"
    res += f"<div>{text_html}</div>"
    if show_arcs:
        res += f"<div style='margin-top: -2px;'>{arcs_html}</div>"
    if show_phonemes:
        res += f"<div style='margin-top: 2px;'>{phonemes_html}</div>"
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
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2;" if soft_bg else ""
    
    html_output = f"<div style='font-size: {size}px; line-height: {spacing}; {style_bg}'>{full_content}</div>"
    st.markdown(html_output, unsafe_allow_html=True)

def build_controls(key_prefix):
    st.write("### ⚙️ Options d'adaptation DYS (Cumulables)")
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
        
    return show_colors, show_arcs, show_phonemes, word_alt, line_alt, soft_bg, size, spacing

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
