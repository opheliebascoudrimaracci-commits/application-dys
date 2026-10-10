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
                color, phoneme = EXACT_COMPLEX_SOUNDS.get('et', ('#800080', 'è'))
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

def render_word_multilevel(word, show_colors, show_arcs, show_phonemes):
    blocks = parse_word_to_blocks(word)
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block['text']
        r_type = block.get('render_type', 'normal')
        
        if r_type == 'muted':
            part_html = f"<span style='color: #b0b0b0; opacity: 0.5;'>{text}</span>"
        elif r_type == 'highlight' and show_colors and block.get('color'):
            bg_color = block['color'] + '33' 
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
    
    html = f"<span style='display: inline-block; text-align: center; margin-right: 20px; font-family: \"Open Dyslexic\", sans-serif;'>"
    html += f"<div>{w_main}</div>"
    if show_arcs:
        html += f"<div style='font-size: 0.9em; color: #4a90e2; letter-spacing: 4px; margin-top: 2px;'>{w_arcs}</div>"
    if show_phonemes:
        html += f"<div style='font-size: 0.75em; margin-top: 2px;'>{w_ph}</div>"
    html += f"</span>"
    
    return html

def render_full_dys_text(text, show_colors, show_arcs, show_phonemes, word_alt, line_alt, soft_bg, size, spacing):
    if not text:
        return
        
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for word_idx, word in enumerate(words):
            word_html = render_word_multilevel(word, show_colors, show_arcs, show_phonemes)
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
    
    st.markdown(f"<div style='font-size: {size}px; line-height: {spacing}; {style_bg}'>{full_content_adapted}</div>", unsafe_allow_html=True)
    
    st.write("---")
    st.write("### 🖨️ Options d'impression :")
    
    print_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Open Dyslexic', sans-serif;
            margin: 20px;
        }}
        .btn {{
            border: none;
            color: white;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            margin-right: 10px;
            font-family: 'Open Dyslexic', sans-serif;
        }}
        .btn-blue {{ background-color: #4a90e2; }}
        .btn-green {{ background-color: #2e7d32; }}
        
        @media print {{
            .no-print {{ display: none !important; }}
        }}
    </style>
    </head>
    <body>
        <div class="no-print">
            <button class="btn btn-blue" onclick="printSection('corrected')">🖨️ Imprimer version corrigée (Adaptée)</button>
            <button class="btn btn-green" onclick="printSection('training')">📝 Imprimer fiche d'entraînement (Vierge)</button>
        </div>

        <script>
        function printSection(type) {{
            var content = '';
            if (type === 'corrected') {{
                content = `<div style="font-size: {size}px; line-height: {spacing}; font-family: 'Open Dyslexic', sans-serif;">{full_content_adapted}</div>`;
            }} else {{
                content = `
                    <h3 style="margin-bottom: 25px; text-decoration: underline; font-family: 'Open Dyslexic', sans-serif;">Consigne : Entoure ou surligne les sons complexes et les pièges.</h3>
                    <div style="font-size: {size}px; line-height: 3.0; font-family: 'Open Dyslexic', sans-serif;">{full_content_training}</div>
                `;
            }}
            
            var printWindow = window.open('', '_blank');
            printWindow.document.write('<html><head><title>Impression Fiche DYS</title>');
            printWindow.document.write('<link href="https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap" rel="stylesheet">');
            printWindow.document.write("<style>body {{ font-family: 'Open Dyslexic', sans-serif; padding: 20px; }}</style>");
            printWindow.document.write('</head><body>');
            printWindow.document.write(content);
            printWindow.document.write('</body></html>');
            printWindow.document.close();
            printWindow.focus();
            setTimeout(function() {{
                printWindow.print();
                printWindow.close();
            }}, 250);
        }}
        </script>
    </body>
    </html>
    """
    components.html(print_html, height=80)

def show_color_legend():
    """Affiche une légende interactive du code couleur utilisé dans l'application."""
    with st.expander("📖 Légende et Code Couleur Pédagogique"):
        st.markdown("### 🎨 Surlignage des sons complexes (Fond pastel)")
        cols = st.columns(4)
        with cols[0]:
            st.markdown("<span style='background-color: #FF000033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>ou</span> : Son [ou]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #8B451333; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>on</span> : Son [on]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #FF8C0033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>an / en</span> : Son [an]", unsafe_allow_html=True)
        with cols[1]:
            st.markdown("<span style='background-color: #FFD70033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>eau / au / o</span> : Son [o]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #80008033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>et / é / ez</span> : Son [é/è]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #0000FF33; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>eu / oeu</span> : Son [eu]", unsafe_allow_html=True)
        with cols[2]:
            st.markdown("<span style='background-color: #1E4D2B33; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>in / ain</span> : Son [in]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #00000033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>oi</span> : Son [oi]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #DAA52033; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>ch</span> : Son [ch]", unsafe_allow_html=True)
        with cols[3]:
            st.markdown("<span style='background-color: #8e44ad33; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>qu / ph</span> : [k] / [f]", unsafe_allow_html=True)
            st.markdown("<span style='background-color: #16a08533; padding: 2px 6px; font-weight: bold; border-radius: 4px;'>gn</span> : Son [gn]", unsafe_allow_html=True)

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

# Affichage de la légende en haut
show_color_legend()
st.write("---")

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
                render_full_dys_text(ext_txt, **opts2)
            else:
                st.warning("Aucun texte trouvé dans l'image.")
        except Exception as e:
            st.error(f"Erreur d'extraction OCR : {e}")

st.write("---")
st.caption("Ophélie Bascou Drimaracci - Application Pédagogique DYS")
