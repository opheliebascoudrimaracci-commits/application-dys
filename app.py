import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random
import google.generativeai as genai

# Configuration de la clé d'API Gemini depuis vos Secrets Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    

# 1. Configuration unique de la page
st.set_page_config(
    page_title="Ophélie Bascou Drimaracci",
    page_icon="✏️",
    layout="wide"
)

# 2. Injection minimale des polices
st.markdown("<link href='https://fonts.googleapis.com/css2?family=Open+Dyslexic&display=swap' rel='stylesheet'>", unsafe_allow_html=True)

# --- MENU LATÉRAL PRINCIPAL ---
st.sidebar.title("📌 Navigation")
menu_selection = st.sidebar.radio(
    "Choisissez un module :",
    [
        "🏠 Présentation",
        "📄 Aide à la lecture (Texte & OCR)",
        "✨ Générateur d'histoires",
        "🎤 Aide à la dictée"  # <-- S'assurer que cette ligne est présente
    ]
)

PLURAL_SUBJECTS = {
    "ils", "elles", "les", "des", "ces", "mes", "tes", "ses", "nos", "vos", "leurs",
    "deux", "trois", "quatre", "cinq", "plusieurs", "certains", "certaines"
}

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

def parse_word_to_blocks(word, is_plural_verb=False):
    blocks = []
    w_lower = word.lower()
    
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
                if key == 'et':
                    is_word_et = (w_lower == 'et')
                    is_end_of_word = (i + 2 == n)
                    if not (is_word_et or is_end_of_word):
                        continue 
                
                # Exclusions des nasales (in, an, on, en, un)
                if key in ['in', 'an', 'on', 'en', 'un']:
                    next_idx = i + len(key)
                    
                    if key == 'en' and w_lower.endswith('ent') and i == n - 3:
                        if is_plural_verb:
                            continue
                        
                    if next_idx < n and w_lower[next_idx] in VOWELS:
                        continue 
                    if next_idx < n and key[-1] == w_lower[next_idx]:
                        continue

                color, phoneme = EXACT_COMPLEX_SOUNDS[key]
                actual_text = word[i:i+len(key)]
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
            is_final_mute = (i == n - 1 and n > 2 and word[i-1].lower() in VOWELS)
            
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

def render_word_multilevel(word, show_phonemes=True, show_arcs=False, prev_word=""):
    clean_prev = prev_word.strip().lower().strip(".,;:!?()[]{}\"'«»")
    clean_word = word.strip().lower().strip(".,;:!?()[]{}\"'«»")
    
    is_plural_verb = (clean_prev in PLURAL_SUBJECTS) and clean_word.endswith("ent") and len(clean_word) > 4
    blocks = parse_word_to_blocks(word, is_plural_verb=is_plural_verb)
    
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block.get('text', '')
        color = block.get('color', '#000000')
        phoneme = block.get('phoneme', '')
        render_type = block.get('render_type', 'normal')
        
        if render_type == 'highlight':
            word_html_parts.append(f"<span style='color: {color}; font-weight: bold;'>{text}</span>")
        elif render_type == 'color_text':
            word_html_parts.append(f"<span style='color: {color};'>{text}</span>")
        elif render_type == 'muted':
            word_html_parts.append(f"<span style='color: #a0a0a0; text-decoration: line-through;'>{text}</span>")
        else:
            word_html_parts.append(f"<span>{text}</span>")
            
        if show_phonemes and phoneme:
            ph_color = color if color else '#555555'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-size: 0.75em;'>{phoneme}</span>")
        else:
            phoneme_html_parts.append(f"<span style='font-size: 0.75em;'>&nbsp;</span>")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""
    
    num_syllables = count_syllables_approx(word)
    w_arcs = " ".join(["•"] * num_syllables) if show_arcs else ""
    
    html = f"<span style='display: inline-block; text-align: center; margin: 0 3px; vertical-align: top;'>"
    html += f"<div>{w_main}</div>"
    if show_arcs:
        html += f"<div style='font-size: 0.7em; color: #888888; margin-top: -4px;'>{w_arcs}</div>"
    if show_phonemes:
        html += f"<div style='font-size: 0.8em; margin-top: 1px;'>{w_ph}</div>"
    html += "</span>"
    
    return html

def render_full_dys_text(text, show_phonemes=True, show_colors=True, word_alt=False, line_alt=False, size=18, soft_bg=True, **kwargs):
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for idx, word in enumerate(words):
            prev_word = words[idx - 1] if idx > 0 else ""
            word_html = render_word_multilevel(word, show_phonemes=show_phonemes, prev_word=prev_word)
            
            if word_alt and not show_colors:
                color = "#0055ff" if idx % 2 == 0 else "#cc0000"
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
    
    if soft_bg:
        style_bg = (
            "background-color: #f4f6f9; "
            "padding: 15px; "
            "border-radius: 8px; "
            "border-left: 5px solid #4a90e2; "
            "color: #111111;"
        )
    else:
        style_bg = ""
    
    st.markdown("### 👁️ Aperçu adapté :")
    st.markdown(f"<div style='font-size: {size}px; {style_bg}'>{full_content_adapted}</div>", unsafe_allow_html=True)
    
    html_export_adapte = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Texte Adapté</title>
    </head>
    <body style="font-size: {size}px; {style_bg}">
        {full_content_adapted}
    </body>
    </html>
    """
    
    st.download_button(
        label="📥 Télécharger / Imprimer le texte adapté (avec couleurs et aides)",
        data=html_export_adapte,
        file_name="texte_adapte_dys.html",
        mime="text/html"
    )

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

def show_color_legend():
    st.markdown("**Légende des couleurs et des sons :**")
    st.markdown("Les sons complexes et les indices visuels sont adaptés pour faciliter la lecture.")

# ==========================================
# GESTION DES PAGES DU MENU LATÉRAL
# ==========================================

if menu_selection == "🏠 Présentation":
    st.title("✏️ Application Pédagogique & Adaptation DYS")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("---")
    st.markdown("""
    Bienvenue sur cette application pédagogique conçue pour faciliter l'accès à la lecture 
    et accompagner les enfants et élèves présentant des troubles **DYS** (dyslexie, dyspraxie).
    
    ### 🌟 Ce que propose l'application :
    * **📄 Aide à la lecture de texte** : Saisissez ou collez n'importe quel texte pour l'adapter instantanément.
    * **📷 Importation OCR** : Prenez en photo un livre ou une feuille pour en extraire le texte et l'adapter.
    * **✨ Générateur d'histoires magiques** : Créez des histoires personnalisées selon différents niveaux de difficulté.
    * **🎨 Code couleur et phonèmes** : Coloration des sons complexes, gestion des lettres muettes, des liaisons et des accords au pluriel.
    """)

elif menu_selection == "📄 Aide à la lecture (Texte & OCR)":
    st.title("📄 Aide à la lecture & OCR")
    st.subheader("Ophélie Bascou Drimaracci")
    
    tab1, tab2 = st.tabs(["📄 Saisie / Coller du texte", "📷 Importer une image (OCR)"])
    
    with tab1:
        st.write("### Saisir ou coller un texte")
        txt = st.text_area("Entrez votre texte ici :", height=140, placeholder="Tapez ou collez votre texte...")
        if txt:
            st.write("---")
            opts = build_controls("t1")
            render_full_dys_text(txt, **opts)

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
                    render_full_dys_text(ext_txt, **opts2)
                else:
                    st.warning("Aucun texte trouvé. Assurez-vous que l'éclairage est bon et que le texte est bien net.")
            except Exception as e:
                st.error(f"Erreur d'extraction OCR : {e}")

elif menu_selection == "✨ Générateur d'histoires":
    st.title("✨ Générateur d'histoires magiques")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("Créez une histoire sur-mesure en choisissant son niveau de difficulté et le prénom du héros !")

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

        if st.button("✨ Générer l'histoire magique avec l'IA", type="primary", key="btn_generer_histoire"):
        h = nom_personnage.strip() if nom_personnage.strip() else "Le héros"
        
        prompt_ia = "Écris une histoire pour enfants douce, captivante et adaptée en français. Le héros s'appelle " + h + ". "

        prompt_ia = "Écris une histoire pour enfants douce, captivante et adaptée en français. Le héros s'appelle " + h + ". "
        if "Niveau 1" in niveau_histoire:
            prompt_ia += "L'histoire doit faire exactement 5 à 6 phrases très simples avec du vocabulaire facile, parfaite pour un débutant en lecture."
        elif "Niveau 2" in niveau_histoire:
            prompt_ia += "L'histoire doit faire environ 10 phrases avec un vocabulaire enrichi et une petite péripétie."
        else:
            prompt_ia += "L'histoire doit faire environ 20 phrases, très riche en détails, avec un véritable récit captivant et un beau dénouement."
            
        with st.spinner("🤖 L'IA invente votre histoire sur-mesure..."):
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt_ia)
                st.session_state['histoire_generee'] = response.text.strip()
            except Exception as e:
                st.warning("Mode secours (génération hors-ligne) :")
                st.session_state['histoire_generee'] = h + " part à l'aventure dans une grande forêt magique. Il croise un petit oiseau bleu qui chante une belle mélodie. Ensemble, ils découvrent un trésor caché au pied d'un grand arbre. Content de sa journée, " + h + " rentre chez lui le cœur joyeux."

        # Options d'adaptation DYS sur l'histoire
        opts3 = build_controls("t3")
        render_full_dys_text(st.session_state['histoire_generee'], **opts3)

# ==========================================
# MODULE : AIDE À LA DICTÉE
# ==========================================
elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("Saisissez jusqu'à 20 mots à réviser. L'application générera vos fiches de travail prêtes à être imprimées !")
    
    st.write("---")
    
    # 1. Zone de saisie des mots
    input_text = st.text_area(
        "Entrez vos mots (séparés par un espace, une virgule ou une ligne) :",
        height=120,
        placeholder="Exemple: bateau maison cheval oiseau fleur château garçon soleil chêne dragon..."
    )
    
    # Extraction et nettoyage des mots (max 20 mots)
    raw_words = re.split(r'[\s,\n]+', input_text.strip())
    words_list = [w.strip() for w in raw_words if w.strip()][:20]
    
    if words_list:
        st.success(f"📋 **{len(words_list)} mot(s) enregistré(s)** : {', '.join(words_list)}")
        st.write("---")
        
        dic_tab1, dic_tab2, dic_tab3, dic_tab4 = st.tabs([
            "Page 1 : 🎨 Mots codés DYS",
            "Page 2 : ✂️ Mots découpés",
            "Page 3 : ✏️ Mots à trous",
            "Page 4 : 📝 Phrases à trous"
        ])
        
        # PAGE 1 : Mots avec codes DYS
        with dic_tab1:
            st.write("### Page 1 : Fiche de révision avec codes visuels DYS")
            p1_html_parts = []
            for w in words_list:
                coded_w = render_word_multilevel(w, show_phonemes=True)
                p1_html_parts.append(f"<div style='display: inline-block; margin: 15px; font-size: 26px;'>{coded_w}</div>")
            
            p1_content = "".join(p1_html_parts)
            st.markdown(f"<div style='background-color: #f4f6f9; padding: 20px; border-radius: 10px;'>{p1_content}</div>", unsafe_allow_html=True)
            
            p1_export = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head><meta charset="UTF-8"><title>Page 1 - Mots Codés DYS</title></head>
            <body style="font-family: sans-serif; padding: 30px;">
                <h1 style="text-align: center;">Fiche de Révision - Dictée</h1>
                <hr><br>
                <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 28px;">
                    {p1_content}
                </div>
            </body>
            </html>
            """
            st.download_button("📥 Télécharger / Imprimer la Page 1 (HTML)", data=p1_export, file_name="page1_mots_codes.html", mime="text/html")
            
        # PAGE 2 : Mots découpés (Carrés)
        with dic_tab2:
            st.write("### Page 2 : Mots avec lettres séparées par des carrés (à découper)")
            p2_html_parts = []
            for w in words_list:
                letters_squares = []
                for char in w:
                    letters_squares.append(
                        f"<span style='display: inline-block; width: 40px; height: 40px; border: 2px solid #333; margin: 2px; text-align: center; line-height: 40px; font-weight: bold; font-size: 22px;'>{char}</span>"
                    )
                word_box = f"<div style='margin-bottom: 20px;'><span style='display: inline-block; margin-right: 15px; font-weight: bold; font-size: 18px; min-width: 120px;'>{w} :</span> {''.join(letters_squares)}</div>"
                p2_html_parts.append(word_box)
                
            p2_content = "".join(p2_html_parts)
            st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border: 1px dashed #ccc; border-radius: 10px;'>{p2_content}</div>", unsafe_allow_html=True)
            
            p2_export = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head><meta charset="UTF-8"><title>Page 2 - Mots à découper</title></head>

f"""
# ==========================================
# MODULE : AIDE À LA DICTÉE (AVEC IA)
# ==========================================
elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("Saisissez jusqu'à 20 mots. L'IA générera automatiquement une vraie phrase logique les mettant en contexte !")
    
    st.write("---")
    
    input_text = st.text_area(
        "Entrez vos mots (séparés par un espace, une virgule ou une ligne) :",
        height=120,
        placeholder="Exemple: bateau maison cheval oiseau fleur château garçon soleil chêne dragon..."
    )
    
    raw_words = re.split(r'[\s,\n]+', input_text.strip())
    words_list = [w.strip() for w in raw_words if w.strip()][:20]
    
    if words_list:
        st.success(f"📋 **{len(words_list)} mot(s) enregistré(s)** : {', '.join(words_list)}")
        st.write("---")
        
        dic_tab1, dic_tab2, dic_tab3, dic_tab4 = st.tabs([
            "Page 1 : 🎨 Mots codés DYS",
            "Page 2 : ✂️ Mots découpés",
            "Page 3 : ✏️ Mots à trous",
            "Page 4 : 📝 Phrase de dictée (IA)"
        ])
        
        # PAGE 1 : Mots avec codes DYS
        with dic_tab1:
            st.write("### Page 1 : Fiche de révision avec codes visuels DYS")
            p1_html_parts = []
            for w in words_list:
                coded_w = render_word_multilevel(w, show_phonemes=True)
                p1_html_parts.append(f"<div style='display: inline-block; margin: 15px; font-size: 26px;'>{coded_w}</div>")
            
            p1_content = "".join(p1_html_parts)
            st.markdown(f"<div style='background-color: #f4f6f9; padding: 20px; border-radius: 10px;'>{p1_content}</div>", unsafe_allow_html=True)
            
            p1_export = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head><meta charset="UTF-8"><title>Page 1 - Mots Codés DYS</title></head>
            <body style="font-family: sans-serif; padding: 30px;">
                <h1 style="text-align: center;">Fiche de Révision - Dictée</h1>
                <hr><br>
                <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 28px;">
                    {p1_content}
                </div>
            </body>
            </html>
            """
            st.download_button("📥 Télécharger / Imprimer la Page 1 (HTML)", data=p1_export, file_name="page1_mots_codes.html", mime="text/html")
            
        # PAGE 2 : Mots découpés (Carrés)
        with dic_tab2:
            st.write("### Page 2 : Mots avec lettres séparées par des carrés (à découper)")
            p2_html_parts = []
            for w in words_list:
                letters_squares = []
                for char in w:
                    letters_squares.append(
                        f"<span style='display: inline-block; width: 40px; height: 40px; border: 2px solid #333; margin: 2px; text-align: center; line-height: 40px; font-weight: bold; font-size: 22px;'>{char}</span>"
                    )
                word_box = f"<div style='margin-bottom: 20px;'><span style='display: inline-block; margin-right: 15px; font-weight: bold; font-size: 18px; min-width: 120px;'>{w} :</span> {''.join(letters_squares)}</div>"
                p2_html_parts.append(word_box)
                
            p2_content = "".join(p2_html_parts)
            st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border: 1px dashed #ccc; border-radius: 10px;'>{p2_content}</div>", unsafe_allow_html=True)
            
            p2_export = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head><meta charset="UTF-8"><title>Page 2 - Mots à découper</title></head>
            <body style="font-family: sans-serif; padding: 30px;">
                <h1 style="text-align: center;">Étiquettes à découper</h1>
                <hr><br>
                {p2_content}
            </body>
            </html>
            """
            st.download_button("📥 Télécharger / Imprimer la Page 2 (HTML)", data=p2_export, file_name="page2_mots_a_decouper.html", mime="text/html")
            
        # PAGE 3 : Dictée à trous (mots isolés)
        with dic_tab3:
            st.write("### Page 3 : Dictée à trous (Sons et lettres complexes masqués)")
            p3_html_parts = []
            for w in words_list:
                blocks = parse_word_to_blocks(w)
                word_holes = []
                for b in blocks:
                    if b.get('render_type') in ['highlight', 'muted']:

# ==========================================
# MODULE : AIDE À LA DICTÉE (AVEC IA)
# ==========================================
elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("Saisissez jusqu'à 20 mots. L'IA générera automatiquement une vraie phrase logique les mettant en contexte !")
    
    st.write("---")
    
    input_text = st.text_area(
        "Entrez vos mots (séparés par un espace, une virgule ou une ligne) :",
        height=120,
        placeholder="Exemple: bateau maison cheval oiseau fleur château garçon soleil chêne dragon..."
    )
    
    raw_words = re.split(r'[\s,\n]+', input_text.strip())
    words_list = [w.strip() for w in raw_words if w.strip()][:20]
    
    if words_list:
        st.success("📋 **" + str(len(words_list)) + " mot(s) enregistré(s)** : " + ", ".join(words_list))
        st.write("---")
        
        dic_tab1, dic_tab2, dic_tab3, dic_tab4 = st.tabs([
            "Page 1 : 🎨 Mots codés DYS",
            "Page 2 : ✂️ Mots découpés",
            "Page 3 : ✏️ Mots à trous",
            "Page 4 : 📝 Phrase de dictée (IA)"
        ])
        
        # PAGE 1 : Mots avec codes DYS
        with dic_tab1:
            st.write("### Page 1 : Fiche de révision avec codes visuels DYS")
            p1_html_parts = []
            for w in words_list:
                coded_w = render_word_multilevel(w, show_phonemes=True)
                p1_html_parts.append("<div style='display: inline-block; margin: 15px; font-size: 26px;'>" + coded_w + "</div>")
            
            p1_content = "".join(p1_html_parts)
            st.markdown("<div style='background-color: #f4f6f9; padding: 20px; border-radius: 10px;'>" + p1_content + "</div>", unsafe_allow_html=True)
            
            p1_export = "<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 1</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Fiche de Révision - Dictée</h1><hr><br><div style='display: flex; flex-wrap: wrap; gap: 20px; font-size: 28px;'>" + p1_content + "</div></body></html>"
            
            st.download_button("📥 Télécharger / Imprimer la Page 1 (HTML)", data=p1_export, file_name="page1_mots_codes.html", mime="text/html")
            
        # PAGE 2 : Mots découpés (Carrés)
        with dic_tab2:
            st.write("### Page 2 : Mots avec lettres séparées par des carrés (à découper)")
            p2_html_parts = []
            for w in words_list:
                letters_squares = []
                for char in w:
                    letters_squares.append(
                        "<span style='display: inline-block; width: 40px; height: 40px; border: 2px solid #333; margin: 2px; text-align: center; line-height: 40px; font-weight: bold; font-size: 22px;'>" + char + "</span>"
                    )
                word_box = "<div style='margin-bottom: 20px;'><span style='display: inline-block; margin-right: 15px; font-weight: bold; font-size: 18px; min-width: 120px;'>" + w + " :</span> " + "".join(letters_squares) + "</div>"
                p2_html_parts.append(word_box)
                
            p2_content = "".join(p2_html_parts)
            st.markdown("<div style='background-color: #ffffff; padding: 20px; border: 1px dashed #ccc; border-radius: 10px;'>" + p2_content + "</div>", unsafe_allow_html=True)
            
            p2_export = "<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 2</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Étiquettes à découper</h1><hr><br>" + p2_content + "</body></html>"
            
            st.download_button("📥 Télécharger / Imprimer la Page 2 (HTML)", data=p2_export, file_name="page2_mots_a_decouper.html", mime="text/html")
            
        # PAGE 3 : Dictée à trous (mots isolés)
        with dic_tab3:
            st.write("### Page 3 : Dictée à trous (Sons et lettres complexes masqués)")
            p3_html_parts = []
            for w in words_list:
                blocks = parse_word_to_blocks(w)
                word_holes = []
                for b in blocks:
                    if b.get('render_type') in ['highlight', 'muted']:
                        word_holes.append("<span style='display: inline-block; min-width: 35px; border-bottom: 2px solid #000; margin: 0 2px;'>&nbsp;</span>")
                    else:
                        word_holes.append("<span>" + str(b.get('text')) + "</span>")
                
                hole_box = "<div style='font-size: 26px; margin: 15px; display: inline-block; min-width: 200px;'>" + "".join(word_holes) + "</div>"
                p3_html_parts.append(hole_box)
                
            p3_content = "".join(p3_html_parts)
            st.markdown("<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px;'>" + p3_content + "</div>", unsafe_allow_html=True)
            
            p3_export = "<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 3</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Dictée à trous - Mots isolés</h1><hr><br><div style='display: flex; flex-wrap: wrap; gap: 30px; font-size: 30px;'>" + p3_content + "</div></body></html>"
            
            st.download_button("📥 Télécharger / Imprimer la Page 3 (HTML)", data=p3_export, file_name="page3_dictee_a_trous.html", mime="text/html")

        # PAGE 4 : Phrase de dictée IA en contexte
        with dic_tab4:
            st.write("### Page 4 : Phrase de dictée créée par l'IA en contexte")
            
            if st.button("🤖 Générer la phrase de dictée avec l'IA", type="primary", key="btn_gen_phrase_ia"):
                prompt_phrase = "Écris une ou deux phrases grammaticalement correctes et simples en français qui contiennent obligatoirement TOUS les mots suivants : " + ", ".join(words_list) + ". Ne donne aucune explication, uniquement le texte de la phrase."
                
                with st.spinner("L'IA génère la phrase de dictée..."):
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        res = model.generate_content(prompt_phrase)
                        st.session_state['phrase_ia_dictee'] = res.text.strip()
                    except Exception:
                        st.session_state['phrase_ia_dictee'] = "Aujourd'hui nous révisons les mots : " + ", ".join(words_list) + "."
            
            phrase_base = st.session_state.get('phrase_ia_dictee', "Aujourd'hui nous révisons les mots : " + ", ".join(words_list) + ".")
            
            # Application automatique des trous sur la phrase générée
            phrase_trous = phrase_base
            for w in words_list:
                pattern = re.compile(re.escape(w), re.IGNORECASE)
                hole = "<span style='display: inline-block; min-width: 70px; border-bottom: 2px solid #000; margin: 0 4px;'>&nbsp;</span>"
                phrase_trous = pattern.sub(hole, phrase_trous)
                
            st.markdown("<div style='background-color: #ffffff; padding: 25px; border: 1px solid #ddd; border-radius: 10px; font-size: 24px; line-height: 2.2;'>" + phrase_trous + "</div>", unsafe_allow_html=True)
            
            p4_export = "<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 4</title></head><body style='font-family: sans-serif; padding: 40px; font-size: 26px; line-height: 2.5;'><h1 style='text-align: center;'>Dictée de phrases en contexte</h1><hr><br><div>" + phrase_trous + "</div></body></html>"
            
            st.download_button("📥 Télécharger / Imprimer la Page 4 (HTML)", data=p4_export, file_name="page4_phrase_dictee_a_trous.html", mime="text/html")
    else:
        st.info("💡 Veuillez saisir au moins un mot ci-dessus pour générer les 4 pages de travail.")
            
