import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random

# 1. Configuration unique de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci",
    page_icon="✏️",
    layout="wide"
)

# 2. Injection minimale des polices
st.markdown("<link href='https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap' rel='stylesheet'>", unsafe_allow_html=True)

st.title("✏️ Application Pédagogique & Adaptation DYS")
st.subheader("Ophélie Bascou Drimaracci")

tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])

# Dictionnaire des sons complexes
EXACT_COMPLEX_SOUNDS = {
    'eau': ('#FFD700', 'o'),
    'au': ('#FFD700', 'o'),
    'oeu': ('#0066FF', 'eu'),
    'eu': ('#0066FF', 'eu'),
    'ain': ('#0E6636', 'in'),
    'ein': ('#0E6636', 'in'),
    'in': ('#0E6636', 'in'),
    'on': ('#6E2C00', 'on'),
    'un': ('#B9770E', 'un'),
    'ou': ('#FF0000', 'ou'),
    'an': ('#E67E22', 'an'),
    'en': ('#E67E22', 'an'),
    'et': ('#8E44AD', 'é'),
    'ez': ('#8E44AD', 'é'),
    'er': ('#8E44AD', 'é'),
    'ai': ('#C0392B', 'è'),
    'ei': ('#C0392B', 'è'),
    'ch': ('#D4AC0D', 'ch'),
    'ge': ('#C2185B', 'j'),
    'oi': ('#212F3D', 'oi'),
    'oin': ('#D35400', 'oin'),
    'ien': ('#CA6F1E', 'ien'),
    'ph': ('#8E44AD', 'f'),
    'gn': ('#16A085', 'gn'),
    'qu': ('#8E44AD', 'k'),
    'o': ('#FFD700', 'o'),
    'é': ('#8E44AD', 'é'),
}

VOWELS = "aeiouyàâäéèêëïîôöùûüÿ"

def count_syllables(word):
    w = word.strip().lower().strip(".,;:!?()[]{}\"'«»")
    if not w:
        return 0
    exceptions = {
        "bonjour": 2, "napoléon": 4, "comment": 2, "mathis": 2, "théâtre": 2,
        "dans": 1, "une": 1, "tu": 1, "vas": 1, "je": 1, "m'appelle": 2,
        "aujourd'hui": 3, "oiseau": 2, "beaucoup": 2, "famille": 2, "fille": 1,
        "maison": 2, "cheval": 2, "bateau": 2, "ordinateur": 4, "magnifique": 3,
        "maminounou": 4,
    }
    if w in exceptions:
        return exceptions[w]
    if "'" in w or "’" in w:
        parts = re.split(r"['’]", w)
        return sum(count_syllables(p) for p in parts if p)
    w = w.replace("-", "")
    noyaux = re.findall(r'[aeiouyàâäéèêëïîôöùûüÿ]+', w)
    count = len(noyaux)
    if w.endswith("e") and not w.endswith(("ée", "ie", "ue", "eau")) and len(w) > 2:
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
    
    # Règle nette et prioritaire pour les mots commençant par ann-
    if w_lower in ["s'annonce", "annonce"]:
        return [
            {'text': "s", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': "'", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': "an", 'is_muted': False, 'render_type': 'highlight', 'color': '#E67E22', 'phoneme': 'an'},
            {'text': "n", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': "on", 'is_muted': False, 'render_type': 'highlight', 'color': '#6E2C00', 'phoneme': 'on'},
            {'text': "c", 'is_muted': False, 'render_type': 'color_text', 'color': '#059669', 'phoneme': 's'},
            {'text': "e", 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None}
        ]

    if w_lower == "est":
        return [{'text': word, 'is_muted': False, 'render_type': 'highlight', 'color': '#8E44AD', 'phoneme': 'è'}]
    
    if w_lower == "c'est":
        return [
            {'text': 'c', 'is_muted': False, 'render_type': 'color_text', 'color': '#2563eb', 'phoneme': 'k'},
            {'text': "'", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': 'est', 'is_muted': False, 'render_type': 'highlight', 'color': '#8E44AD', 'phoneme': 'è'}
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
                if key in ['in', 'an', 'on', 'en', 'un']:
                    next_idx = i + len(key)
                    if next_idx < n and w_lower[next_idx] in VOWELS:
                        continue 

                color, phoneme = EXACT_COMPLEX_SOUNDS[key]
                
                # Capture propre des nasales avec consonne double (ex: ann -> an + n)
                actual_text = word[i:i+len(key)]
                if key in ['an', 'en', 'in', 'on', 'un'] and i + len(key) < n and word[i+len(key)].lower() == key[-1]:
                    actual_text += word[i+len(key)]
                    blocks.append({
                        'text': actual_text,
                        'is_muted': False,
                        'render_type': 'highlight',
                        'color': color,
                        'phoneme': phoneme
                    })
                    i += len(key) + 1
                    matched_complex = True
                    break
                
                blocks.append({
                    'text': actual_text,
                    'is_muted': False,
                    'render_type': 'highlight',
                    'color': color,
                    'phoneme': phoneme
                })
                i += len(key)
                matched_complex = True
                break
        if matched_complex:
            continue

        if i + 1 < n and c_lower in ['p', 't', 'm', 'n', 'l', 'b', 'd', 'f', 'r', 's'] and word[i+1].lower() == c_lower:
            blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue

        if c_lower == 'e':
            is_before_double = (i + 2 < n and word[i+1].lower() == word[i+2].lower())
            is_final_mute = (i == n - 1 and n > 2)
            
            if is_before_double:
                color, phoneme = EXACT_COMPLEX_SOUNDS.get('et', ('#8E44AD', 'è'))
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'highlight', 'color': color, 'phoneme': phoneme})
                i += 1
                continue
            elif is_final_mute:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
                i += 1
                continue

        if c_lower == 'c':
            next_char = word[i+1].lower() if i + 1 < n else ''
            if next_char in ['e', 'i', 'y']:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': '#059669', 'phoneme': 's'})
            elif next_char not in ['h', '']:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': '#2563eb', 'phoneme': 'k'})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue
            
        if c_lower == 's':
            is_prev_vowel = (i > 0 and word[i-1].lower() in VOWELS)
            is_next_vowel = (i + 1 < n and word[i+1].lower() in VOWELS)
            is_final = (i == n - 1)
            
            if is_prev_vowel and is_next_vowel:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': '#0d9488', 'phoneme': 'z'})
            elif is_final:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue

        if i == n - 1 and c_lower in ['t', 'd', 'x'] and n > 2:
            blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 1
            continue

        blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
        i += 1
        
    return blocks

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes, font_family):
    blocks = parse_word_to_blocks(word)
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block['text']
        r_type = block.get('render_type', 'normal')
        
        if r_type == 'muted':
            part_html = f"<span style='color: #b0b0b0; opacity: 0.5;'>{text}</span>"
        elif r_type == 'highlight' and show_colors and block.get('color'):
            bg_color = block['color'] + '73' 
            part_html = f"<span style='background-color: {bg_color}; padding: 2px 4px; border-radius: 4px; font-weight: bold;'>{text}</span>"
        elif r_type == 'color_text' and show_colors and block.get('color'):
            part_html = f"<span style='color: {block['color']}; font-weight: bold;'>{text}</span>"
        else:
            part_html = text
            
        word_html_parts.append(part_html)
        
        if show_phonemes and block.get('phoneme'):
            ph_color = block.get('color') if (block.get('color') and show_colors) else '#000000'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-weight: bold;'>[{block['phoneme']}]</span>")
        else:
            phoneme_html_parts.append("<span style='visibility: hidden;'>•</span>")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""
    
    num_syllables = count_syllables_approx(word) if show_arcs else 0
    w_arcs = " ".join(["•"] * num_syllables) if show_arcs else ""
    
    html = f"<span style='display: inline-block; text-align: center; margin-right: 20px; font-family: {font_family};'>"
    html += f"<div>{w_main}</div>"
    if show_arcs:
        html += f"<div style='font-size: 0.9em; color: #4a90e2; letter-spacing: 4px; margin-top: 2px;'>{w_arcs}</div>"
    if show_phonemes:
        html += f"<div style='font-size: 0.75em; margin-top: 2px;'>{w_ph}</div>"
    html += f"</span>"
    
    return html

def render_full_dys_text(text, show_colors, show_arcs, show_phonemes, word_alt, line_alt, soft_bg, size, spacing, font_choice, export_key="default"):
    if not text:
        return

    fonts_map = {
        "OpenDyslexic (Police DYS spécialisée)": "'Open Dyslexic', sans-serif",
        "Comic Sans MS / Lexie Readable (Anti-confusion b/d)": "'Comic Sans MS', 'Comic Sans', cursive, sans-serif",
        "Arial / Luciole (Grande clarté)": "Arial, sans-serif"
    }
    font_family = fonts_map.get(font_choice, "'Open Dyslexic', sans-serif")
        
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for word_idx, word in enumerate(words):
            word_html = render_word_multilevel(word, show_colors, show_arcs, show_phonemes, font_family)
            if word_alt and not show_colors:
                color = "#0055ff" if word_idx % 2 == 0 else "#cc0000"
                word_html = f"<span style='color: {color}; font-weight: bold;'>{word_html}</span>"
            rendered_words_adapted.append(word_html)
            
            training_word_html = f"<span style='display: inline-block; margin-right: 18px;'>{word}</span>"
            rendered_words_training.append(training_word_html)
            
        line_content_adapted = " ".join(rendered_words_adapted)
        if line_alt and not show_colors:
            line_color = "#0055ff" if line_idx % 2 == 0 else "#cc0000"
            line_content_adapted = f"<div style='color: {line_color};'>{line_content_adapted}</div>"
            
        rendered_lines_adapted.append(line_content_adapted)
        rendered_lines_training.append(" ".join(rendered_words_training))
        
    full_content_adapted = "<br><br>".join(rendered_lines_adapted)
    full_content_training = "<br><br><br>".join(rendered_lines_training)
    
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2; color: #111111;" if soft_bg else ""
    
    st.markdown("### 👁️ Aperçu adapté :")
    st.markdown(f"<div style='font-size: {size}px; line-height: {spacing}; font-family: {font_family}; {style_bg}'>{full_content_adapted}</div>", unsafe_allow_html=True)
    
    html_export_adapte = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Texte Adapté DYS</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: {font_family}; padding: 30px; background-color: #FFFFFF; color: #000000; font-size: {size}px; line-height: {spacing}; }}
    </style>
    </head>
    <body>
        <div>{full_content_adapted}</div>
    </body>
    </html>
    """
    st.download_button(
        label="📥 Télécharger / Imprimer le texte adapté (avec couleurs et aides)",
        data=html_export_adapte,
        file_name="texte_adapte_dys.html",
        mime="text/html",
        key=f"dl_adapt_{export_key}"
    )
    
    st.markdown("---")
    st.markdown("### 📝 Aperçu de la fiche d'entraînement (Vierge) :")
    st.markdown("<p style='font-weight: bold; text-decoration: underline;'>Consigne : Entoure ou surligne les sons complexes et les pièges.</p>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: {size}px; line-height: 3.0; font-family: {font_family}; background-color: #f0fdf4; padding: 15px; border: 3px solid #84cc16; border-radius: 8px;'>{full_content_training}</div>", unsafe_allow_html=True)
    
    html_fiche_vierge = (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Fiche d'entrainement DYS</title>\n"
        '<link href="https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap" rel="stylesheet">\n'
        "<style>\n"
        f"    body {{ font-family: {font_family}; padding: 30px; background-color: #FFFFFF; color: #000000; }}\n"
        '    .consigne {{ margin-bottom: 25px; text-decoration: underline; font-weight: bold; font-size: 18px; }}\n'
        f"    .cadre {{ font-size: {size}px; line-height: 3.0; padding: 20px; border: 3px solid #84cc16; border-radius: 8px; background-color: #f0fdf4; }}\n"
        "</style>\n</head>\n<body>\n"
        '    <div class="consigne">Consigne : Entoure ou surligne les sons complexes et les pièges.</div>\n'
        f'    <div class="cadre">{full_content_training}</div>\n'
        "</body>\n</html>"
    )

    st.download_button(
        label="📥 Télécharger la fiche d'entraînement vierge (Prête à imprimer)",
        data=html_fiche_vierge,
        file_name="fiche_entrainement_dys.html",
        mime="text/html",
        key=f"dl_vierge_{export_key}"
    )
    st.caption("💡 Astuce : Ouvrez le fichier téléchargé sur votre téléphone pour l'imprimer directement via le menu de votre navigateur.")

def show_color_legend():
    with st.expander("📖 Légende et Code Couleur Pédagogique"):
        st.markdown("### 🧠 Surlignage des sons complexes (Fond pastel soutenu)")
        cols = st.columns(4)
        with cols[0]:
            st.markdown("<span style='background-color: #FF000073; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>ou</span> : Son [ou] (Rouge vif)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #6E2C0073; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>on</span> : Son [on] (Marron)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #E67E2273; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>an / en</span> : Son [an] (Orange)", unsafe_allow_html=True)
        with cols[1]:
            st.markdown("<span style='background-color: #FFD70073; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>eau / au / o</span> : Son [o] (Jaune)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #8E44AD73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>et / é / ez</span> : Son [é/è] (Violet)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #0066FF73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>eu / oeu</span> : Son [eu] (Bleu)", unsafe_allow_html=True)
        with cols[2]:
            st.markdown("<span style='background-color: #0E663673; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>in / ain</span> : Son [in] (Vert sapin)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #212F3D73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>oi</span> : Son [oi] (Noir)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #D4AC0D73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>ch</span> : Son [ch] (Moutarde)", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #C2185B73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>ge</span> : Son [j] (Rose)", unsafe_allow_html=True)
        with cols[3]:
            st.markdown("<span style='background-color: #8E44AD73; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>qu / ph</span> : [k] / [f]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #16A08573; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>gn</span> : Son [gn] (Turquoise)", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔤 Couleur des lettres contextuelles & Muettes")
        c_cols = st.columns(3)
        with c_cols[0]:
            st.markdown("<span style='color: #2563eb; font-weight: bold;'>C</span> : Son [k] (ex: *cas* e)", unsafe_allow_html=True)
        with c_cols[1]:
            st.markdown("<span style='color: #059669; font-weight: bold;'>C</span> : Son [s] (ex: *c*e)", unsafe_allow_html=True)
        with c_cols[2]:
            st.markdown("<span style='color: #0d9488; font-weight: bold;'>S</span> : Son [z] entre 2 voyelles", unsafe_allow_html=True)
        st.markdown("<span style='color: #b0b0b0; opacity: 0.8; font-weight: bold;'>Lettre grisée</span> : Lettre muette (ex: e, s, t finaux)", unsafe_allow_html=True)

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
        st.write("**Typographie & Police DYS :**")
        font_choice = st.selectbox(
            "Police d'écriture :",
            [
                "OpenDyslexic (Police DYS spécialisée)",
                "Comic Sans MS / Lexie Readable (Anti-confusion b/d)",
                "Arial / Luciole (Grande clarté)"
            ],
            key=f"{key_prefix}_font"
        )
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
        "spacing": spacing,
        "font_choice": font_choice
    }

show_color_legend()
st.write("---")

# ONGLET 1 : Texte
with tab1:
    st.write("### Saisir ou coller un texte")
    txt = st.text_area("Entrez votre texte ici :", height=140, placeholder="Tapez ou collez votre texte...")
    if txt:
        st.write("---")
        opts = build_controls("t1")
        render_full_dys_text(txt, **opts, export_key="onglet1")

# ONGLET 2 : Appareil photo direct ou Import de fichier
with tab2:
    st.write("### 📷 Capturer ou importer une photo")
    choix_source = st.radio("Méthode :", ["Prendre une photo en direct", "Importer depuis la galerie / un fichier"], key="source_ocr")
    file = st.camera_input("Cliquez pour prendre la photo du texte") if choix_source == "Prendre une photo en direct" else st.file_uploader("Choisissez une image (PNG, JPG)", type=["png", "jpg", "jpeg"], key="file_ocr")

    if file:
        img = Image.open(file)
        st.image(img, caption="Image sélectionnée", use_container_width=True)
        try:
            img_gray = img.convert('L')
            enhancer = ImageEnhance.Contrast(img_gray)
            img_contrast = enhancer.enhance(1.8)
            img_processed = img_contrast.filter(ImageFilter.SHARPEN)
            ext_txt = pytesseract.image_to_string(img_processed, lang="fra", config=r'--oem 3 --psm 6')

            if ext_txt.strip():
                st.success("Texte extrait avec succès !")
                with st.expander("Voir / Modifier le texte extrait"):
                    ext_txt = st.text_area("Texte détecté :", ext_txt, height=120, key="ocr_edit")
                st.write("---")
                opts2 = build_controls("t2")
                render_full_dys_text(ext_txt, **opts2, export_key="onglet2")
            else:
                st.warning("Aucun texte trouvé. Assurez-vous que l'éclairage est bon et que le texte est bien net.")
        except Exception as e:
            st.error(f"Erreur d'extraction OCR : {e}")

# SECTION DÉDIÉE : Le Générateur d'histoires magiques
st.write("---")
st.markdown("## ✨ Générateur d'histoires magiques")
st.write("Créez une histoire sur-mesure en choisissant son niveau de difficulté (Niveau 1 : 5+ phrases, Niveau 2 : 10+ phrases, Niveau 3 : 20+ phrases) et le prénom du héros !")

col_gen1, col_gen2 = st.columns(2)
with col_gen1:
    niveau_histoire = st.selectbox(
        "Niveau de difficulté :",
        ["Niveau 1 : Débutant (5 phrases et +)", "Niveau 2 : Intermédiaire (10 phrases et +)", "Niveau 3 : Avancé (20 phrases et +)"],
        key="select_niveau_histoire"
    )
with col_gen2:
    nom_personnage = st.text_input(
        "Nom du personnage principal :",
        placeholder="Ex: Léo, Léna, Mathis...",
        key="input_nom_personnage"
    )

if st.button("✨ Générer l'histoire magique", type="primary", key="btn_generer_histoire"):
    h = nom_personnage if nom_personnage else "Le héros"
    
    if "Niveau 1" in niveau_histoire:
        phrases_niv1 = [
            f"{h} se réveille dans une petite maison colorée.",
            "Il regarde par la fenêtre et voit un beau soleil.",
            "Le chat de la maison vient lui dire bonjour en miaulant.",
            "Il prend un bon bol de lait chaud avec du pain frais.",
            "Ensuite, il sort dans le jardin pour jouer avec ses amis.",
            "La journée s'annonce calme et très amusante pour tout le monde."
        ]
        st.session_state['histoire_generee'] = " ".join(phrases_niv1)

    elif "Niveau 2" in niveau_histoire:
        phrases_niv2 = [
            f"Il était une fois, un courageux personnage nommé {h} qui adorait l'aventure.",
            "Un beau matin de printemps, il décida de partir à la découverte de la grande forêt mystérieuse.",
            "Sur son chemin, il rencontra un petit oiseau bleu qui chantait une douce mélodie.",
            "L'oiseau décida de l'accompagner pour lui montrer le chemin le plus sûr.",
            "Après une longue marche, ils arrivèrent près d'un ruisseau aux eaux scintillantes.",
            "Ils burent un peu d'eau fraîche et se reposèrent sous un grand chêne centenaire.",
            "Soudain, un écureuil malicieux leur indiqua un sentier caché derrière les buissons.",
            "En suivant ce sentier, {h} découvrit un magnifique coffre en bois sculpté.",
            "À l'intérieur, il y avait des livres magiques et des images pleines de couleurs.",
            "Heureux de sa belle trouvade, il rentra chez lui à la tombée de la nuit pour tout raconter à sa famille."
        ]
        st.session_state['histoire_generee'] = " ".join(phrases_niv2)

    else:  # Niveau 3
        phrases_niv3 = [
            f"Au cœur d'un royaume lointain et paisible, vivait un jeune explorateur nommé {h}.",
            "Depuis son plus jeune âge, il passait des heures à lire des grimoires anciens dans la bibliothèque du village.",
            "Un soir d'automne, en soufflant la poussière d'un vieux livre relié de cuir, il découvrit une carte secrète.",
            "Cette carte indiquait l'emplacement exact de la vallée oubliée, un endroit légendaire où le temps semblait s'être arrêté.",
            "Sans hésiter une seule seconde, {h} prépara son sac à dos avec un peu de nourriture, une gourde et sa boussole dorée.",
            "Il quitta son village au lever du jour, alors que les premiers rayons de soleil doraient les sommets des montagnes.",
            "La première étape de son voyage consistait à traverser la ténébreuse forêt des murmures.",
            "Dans cette forêt, les arbres étaient si hauts qu'ils masquaient presque entièrement la lumière du ciel.",
            "Heureusement, grâce à son grand sens de l'orientation et à son calme, il trouva rapidement la bonne direction.",
            "Il croisa sur son passage des biches élégantes, des hiboux curieux et de jolies fleurs sauvages aux parfums enivrants.",
            "Après avoir franchi la forêt, il se retrouva face au pont de pierre qui enjambait le torrent rugissant.",
            "Le pont était gardé par une vieille statue de pierre représentant un dragon endormi depuis des siècles.",
            "En posant la main sur la patte du dragon, un mécanisme secret s'activa et libéra le passage en douceur.",
            "{h} traversa le pont d'un pas assuré, sentant l'excitation grandir au fond de son cœur.",
            "Il pénétra enfin dans la fameuse vallée oubliée, baignée par une lumière douce et irréelle.",
            "Au centre de la vallée se dressait un magnifique arbre de cristal dont les feuilles brillaient comme des diamants.",
            "Au pied de cet arbre magique reposait un ancien parchemin contenant les secrets des grands sages d'autrefois.",
            "Il prit le temps de lire le texte gravé sur le parchemin, apprenant de merveilleuses histoires sur l'origine du monde.",
            "Le soleil commença lentement à descendre à l'horizon, peignant le ciel de teintes orangées et pourpres.",
            "Le cœur rempli de souvenirs inoubliables et de sagesse, {h} prit le chemin du retour, fier de cette grande aventure.",
            "De retour chez lui, il déposa le parchemin en lieu sûr et s'endormit paisiblement, prêt pour de nouveaux rêves."
        ]
        st.session_state['histoire_generee'] = " ".join(phrases_niv3)

if 'histoire_generee' in st.session_state:
    st.write("---")
    st.markdown("### 📖 Histoire générée :")
    opts_histoire = build_controls("adaptation_histoire")
    st.write("---")
    render_full_dys_text(st.session_state['histoire_generee'], **opts_histoire, export_key="histoire_gen")

st.write("---")
st.caption("Ophélie Bascou Drimaracci - Application Pédagogique DYS")
