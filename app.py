import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random
import hashlib
import json
import streamlit as st
from openai import OpenAI
import google.generativeai as genai

def interroger_ia(prompt_texte, temperature=0.8):
    """
    Fonction centralisée : 
    1. Priorité à Groq (via SDK OpenAI standard, modèles rapides).
    2. Secours automatique sur Gemini (gemini-3.8-flash) en cas de besoin.
    """
    erreurs = []

    # -------------------------------------------------------------
    # 1. TENTATIVE AVEC GROQ (via SDK OpenAI)
    # -------------------------------------------------------------
    groq_key = st.secrets.get("GROQ_API_KEY")
    if groq_key:
        try:
            client = OpenAI(
                api_key=groq_key.strip(),
                base_url="https://api.groq.com/openai/v1",
            )
            # Liste des modèles Groq à tester
            groq_models = [
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "llama3-8b-8192"
            ]
            
            for g_model in groq_models:
                try:
                    response = client.chat.completions.create(
                        model=g_model,
                        messages=[{"role": "user", "content": prompt_texte}],
                        temperature=temperature,
                    )
                    if response.choices and response.choices[0].message.content:
                        return response.choices[0].message.content.strip()
                except Exception as e_inner:
                    erreurs.append(f"Groq ({g_model}): {e_inner}")

        except Exception as e:
            erreurs.append(f"Groq Init: {e}")
    else:
        erreurs.append("Groq: Clé 'GROQ_API_KEY' absente des secrets")

    # -------------------------------------------------------------
    # 2. SECOURS AUTOMATIQUE AVEC GOOGLE GEMINI
    # -------------------------------------------------------------
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key.strip())
            generation_config = {"temperature": temperature}
            
            # Utilisation du modèle actif Gemini
            model = genai.GenerativeModel("gemini-3.8-flash")
            res = model.generate_content(prompt_texte, generation_config=generation_config)
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            erreurs.append(f"Gemini: {e}")
    else:
        erreurs.append("Gemini: Clé 'GEMINI_API_KEY' absente des secrets")

    # Si les deux services échouent, on retourne le bilan des erreurs
    return f"Erreur IA -> " + " | ".join(erreurs)
    


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
        "🎤 Aide à la dictée"
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

def get_syllables_count_ai(word):
    """Interroge Gemini pour obtenir le nombre exact de syllabes d'un mot."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = (
            f"Donne uniquement le nombre de syllabes orales du mot français suivant : '{word}'. "
            "Réponds par un seul chiffre (par exemple : 2)."
        )
        model = genai.GenerativeModel("gemini-2.5-flash")
        res = model.generate_content(prompt)
        
        if res and res.text:
            match = re.search(r'\d+', res.text.strip())
            if match:
                return int(match.group())
    except Exception:
        pass
    return max(1, len(word) // 3)

def count_syllables_approx(word):
    w_clean = word.strip().lower()
    if 'syllables_cache' in st.session_state:
        return st.session_state['syllables_cache'].get(w_clean, max(1, len(w_clean) // 3))
    return max(1, len(w_clean) // 3)

def get_word_syllables(word):
    return count_syllables_approx(word)
                
def parse_word_to_blocks(word, is_plural_verb=False):
    blocks = []
    w_lower = word.lower()
    n = len(word)
    
    if w_lower == "est":
        return [{'text': word, 'is_muted': False, 'render_type': 'highlight', 'color': '#8E44AD', 'phoneme': 'è'}]
    
    if w_lower == "c'est":
        return [
            {'text': 'c', 'is_muted': False, 'render_type': 'color_text', 'color': '#2563eb', 'phoneme': 'k'},
            {'text': "'", 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None},
            {'text': 'est', 'is_muted': False, 'render_type': 'highlight', 'color': '#8E44AD', 'phoneme': 'è'}
        ]

    i = 0
    sorted_keys = sorted(EXACT_COMPLEX_SOUNDS.keys(), key=len, reverse=True)
    
    while i < n:
        if i < n - 1 and w_lower[i:i+2] == 'th':
            blocks.append({'text': word[i], 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            blocks.append({'text': word[i+1], 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 2
            continue

        if i < n - 1 and w_lower[i] == 'g' and w_lower[i+1] in 'eéêëiîïy':
            blocks.append({'text': word[i:i+2], 'is_muted': False, 'render_type': 'highlight', 'color': '#C2185B', 'phoneme': 'j'})
            i += 2
            continue

        char = word[i]
        c_lower = char.lower()
        
        if c_lower == 'h':
            if i == 0 or word[i-1].lower() not in ['c', 'p', 't']:
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

PRENOMS_CONSONNE_FINALE_PRONONCEE = ["mathis", "alexis", "loic", "loïc", "yanis", "iris", "jervis"]

def render_word_multilevel(word, show_phonemes=True, prev_word="", show_arcs=True):
    clean_word_lower = word.lower().strip()
    
    if clean_word_lower in PRENOMS_CONSONNE_FINALE_PRONONCEE:
        return f"<span style='display: inline-block; text-align: center; margin: 0 3px; vertical-align: top;'><div><span style='color: #1e1b4b; font-weight: bold;'>{word}</span></div></span>"
        
    clean_prev = prev_word.strip().lower() if prev_word else ""
    clean_word = word.strip().lower()
    
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
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        
        for idx, word in enumerate(words):
            prev_word = words[idx - 1] if idx > 0 else ""
            word_html = render_word_multilevel(word, show_phonemes=show_phonemes, prev_word=prev_word)
            
            if word_alt and not show_colors:
                color = "#0055ff" if idx % 2 == 0 else "#cc0000"
                word_html = f"<span style='color: {color}; font-weight: bold;'>{word_html}</span>"
                
            rendered_words_adapted.append(word_html)
            
        line_content_adapted = " ".join(rendered_words_adapted)
        if line_alt and not show_colors:
            line_color = "#0055ff" if line_idx % 2 == 0 else "#cc0000"
            line_content_adapted = f"<div style='color: {line_color};'>{line_content_adapted}</div>"
            
        rendered_lines_adapted.append(line_content_adapted)
        
    full_content_adapted = "<br><br>".join(rendered_lines_adapted)
    
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
    * **🎤 Aide à la dictée (Propulsée par l'IA)** : Analyse phonétique intelligente, découpage syllabique et génération de dictées contextuelles.
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
            opts = build_controls("histoire_t1")
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
                    opts2 = build_controls("histoire_t2")
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
        if "Niveau 1" in niveau_histoire:
            prompt_ia += "L'histoire doit faire exactement 5 à 6 phrases très simples avec du vocabulaire facile, parfaite pour un débutant en lecture."
        elif "Niveau 2" in niveau_histoire:
            prompt_ia += "L'histoire doit faire environ 10 phrases avec un vocabulaire enrichi et une petite péripétie."
        else:
            prompt_ia += "L'histoire doit faire environ 20 phrases, très riche en détails, avec un véritable récit captivant et un beau dénouement."
            
        with st.spinner("🤖 L'IA invente votre histoire sur-mesure..."):
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt_ia)
                st.session_state['histoire_generee'] = response.text.strip()
            except Exception as e:
                st.warning("Mode secours (génération hors-ligne) :")
                st.session_state['histoire_generee'] = h + " part à l'aventure dans une grande forêt magique. Il croise un petit oiseau bleu qui chante une belle mélodie. Ensemble, ils découvrent un trésor caché au pied d'un grand arbre. Content de sa journée, " + h + " rentre chez lui le cœur joyeux."

    if 'histoire_generee' in st.session_state:
        st.write("---")
        st.success("📖 Histoire générée :")
        st.write(st.session_state['histoire_generee'])
        
        opts3 = build_controls("histoire_t3")
        render_full_dys_text(st.session_state['histoire_generee'], **opts3)

# ==========================================
# MODULE : AIDE À LA DICTÉE (AVEC IA)
# ==========================================
elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("Saisissez vos mots. L'IA analyse instantanément la phonétique et génère les 4 pages de travail adaptées !")
    
    st.write("---")

    input_text = st.text_area(
        "Entrez vos mots (séparés par un espace, une virgule ou une ligne) :",
        height=120,
        placeholder="Exemple: bateau, chant, poule",
        key="input_mots_dictee_unique"
    )
    
    raw_words = re.split(r'[\s,\n]+', input_text.strip())
    words_list = [w.strip() for w in raw_words if w.strip()][:20]
    
    if words_list:
        st.success(f"📋 **{len(words_list)} mot(s) actif(s)** : " + ", ".join(words_list))
        st.write("---")
        
        file_signature = "_".join(words_list)
        
        dic_tab1, dic_tab2, dic_tab3, dic_tab4 = st.tabs([
            "Page 1 : 🎨 Mots codés DYS",
            "Page 2 : ✂️ Mots découpés",
            "Page 3 : ✏️ Mots à trous",
            "Page 4 : 📝 Phrase contextuelle (IA)"
        ])
        
        # -----------------------------------------
        # PAGE 1 : Mots codés DYS
        # -----------------------------------------

        
        # -----------------------------------------
        # PAGE 1 : Mots codés DYS
        # -----------------------------------------
        with dic_tab1:
            st.markdown("### Page 1 : Fiche de révision visuelle")
            p1_parts = []
            for w in words_list:
                try:
                    coded_w = render_word_multilevel(w, show_phonemes=True)
                except Exception:
                    coded_w = w
                p1_parts.append(f"<div style='display: inline-block; margin: 10px; padding: 10px 15px; background: #ffffff; border: 2px solid #4f46e5; border-radius: 8px; font-size: 24px; color: #000000;'>{coded_w}</div>")
            
            p1_content = "".join(p1_parts)
            st.markdown(f"<div style='background-color: #f4f6f9; padding: 20px; border-radius: 10px;'>{p1_content}</div>", unsafe_allow_html=True)
            
            p1_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 1</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Fiche de Révision - Mots</h1><hr><br><div style='display: flex; flex-wrap: wrap; gap: 20px;'>{p1_content}</div></body></html>"
            st.download_button("📥 Télécharger / Imprimer la Page 1 (HTML)", data=p1_export, file_name=f"page1_{file_signature}.html", mime="text/html", key="dl_p1_final")
            
        # -----------------------------------------
        # PAGE 2 : Mots découpés (Syllabes & Lettres)
        # -----------------------------------------
        with dic_tab2:
            st.markdown("### Page 2 : Mots découpés en syllabes et lettres")
            p2_parts = []
            
            for w in words_list:
                try:
                    letters_html = "".join([
                        f"<div style='display: inline-block; width: 35px; height: 35px; line-height: 35px; margin: 2px; border: 2px solid #1e1b4b; border-radius: 4px; text-align: center; font-size: 20px; font-weight: bold; color: #000000; background: #ffffff;'>{char}</div>"
                        for char in w.strip() if char != " "
                    ])
                    
                    word_box = (
                        f"<div style='margin: 15px 0; padding: 10px; background: #f8fafc; border-left: 4px solid #4f46e5; border-radius: 6px;'>"
                        f"<span style='font-size: 20px; font-weight: bold; margin-right: 15px; color: #1e1b4b;'>{w} :</span>"
                        f"<div style='display: inline-block; vertical-align: middle;'>{letters_html}</div>"
                        f"</div>"
                    )
                    p2_parts.append(word_box)
                except Exception as err:
                    p2_parts.append(f"<div>{w}</div>")
            
            p2_content = "".join(p2_parts)
            st.markdown(p2_content, unsafe_allow_html=True)
            
            p2_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 2 - Mots découpés</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Mots découpés en lettres</h1><hr><br>{p2_content}</body></html>"
            st.download_button("📥 Télécharger / Imprimer la Page 2 (HTML)", data=p2_export, file_name=f"page2_{file_signature}.html", mime="text/html", key=f"dl_p2_final_{file_signature}")

        # -----------------------------------------
        # PAGE 3 : Mots à trous (Trous systématiques)
        # -----------------------------------------
        with dic_tab3:
            st.markdown("### Page 3 : Dictée à trous sur les mots isolés")
            p3_parts = []
            for w in words_list:
                w_clean = w.strip()
                try:
                    blocks = parse_word_to_blocks(w_clean)
                    hole_word_parts = []
                    has_hole = False
                    
                    for block in blocks:
                        text = block.get('text', '')
                        render_type = block.get('render_type', 'normal')
                        is_muted = block.get('is_muted', False)
                        
                        if render_type == 'highlight' or is_muted:
                            hole_word_parts.append("_" * len(text))
                            has_hole = True
                        else:
                            hole_word_parts.append(text)
                            
                    if not has_hole:
                        if len(w_clean) <= 3:
                            coded_w = w_clean[0] + "_" * (len(w_clean) - 1)
                        else:
                            coded_w = w_clean[:1] + "_" * (len(w_clean) - 2) + w_clean[-1]
                    else:
                        coded_w = "".join(hole_word_parts)
                        
                except Exception:
                    coded_w = w_clean[:1] + "_" * max(1, len(w_clean) - 1)
                    
                p3_parts.append(f"<div style='display: inline-block; margin: 10px; padding: 15px 20px; background: #fff; border: 2px solid #4f46e5; border-radius: 8px; font-size: 24px; font-weight: bold; color: #1e1b4b;'>{coded_w}</div>")
            
            p3_content = "".join(p3_parts)
            st.markdown(f"<div style='background-color: #f4f6f9; padding: 20px; border-radius: 10px;'>{p3_content}</div>", unsafe_allow_html=True)
            
            p3_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 3</title></head><body style='font-family: sans-serif; padding: 30px;'><h1 style='text-align: center;'>Dictée à trous - Mots isolés</h1><hr><br><div style='display: flex; flex-wrap: wrap; gap: 20px;'>{p3_content}</div></body></html>"
            st.download_button("📥 Télécharger / Imprimer la Page 3 (HTML)", data=p3_export, file_name=f"page3_{file_signature}.html", mime="text/html", key="dl_p3_final")

        # -----------------------------------------
        # PAGE 4 : Dictée en contexte (IA : Groq en priorité + Gemini en secours)
        # -----------------------------------------
        with dic_tab4:
            st.markdown("### Page 4 : Phrase de dictée en contexte (Générée par l'IA)")
            
            # Sélecteur de niveau scolaire
            niveau_scolaire = st.selectbox(
                "🎯 Choisissez le niveau scolaire de l'enfant :",
                [
                    "Grande Section",
                    "CP",
                    "CE1",
                    "CE2",
                    "CM1",
                    "CM2",
                    "6ème",
                    "5ème",
                    "4ème",
                    "3ème"
                ],
                index=2,  # CE1 par défaut
                key=f"select_niveau_{file_signature}"
            )
            
            # Clefs de session pour mémoriser la génération par niveau
            combined_sig = f"{file_signature}_{niveau_scolaire}"
            session_key_ia = f"phrase_ia_{combined_sig}"
            fallback_phrase = f"Aujourd'hui, nous étudions avec attention les mots suivants : {', '.join(words_list)}."

            # Prompt principal
            prompt_phrase = (
                f"Tu es un professeur expert en pédagogie et élèves DYS. "
                f"Écris une courte dictée originale, claire et parfaitement adaptée au niveau scolaire : **{niveau_scolaire}**. "
                f"Le texte doit intégrer impérativement et naturellement TOUS ces mots : {', '.join(words_list)}. "
                f"Renvoie uniquement le texte de la dictée, sans aucune introduction, sans guillemets et sans commentaires."
            )

            # 1. Génération initiale (si non présente en session)
            if session_key_ia not in st.session_state:
                with st.spinner(f"🤖 L'IA compose une dictée unique pour le niveau {niveau_scolaire}..."):
                    res_ia = interroger_ia(prompt_phrase, temperature=0.8)
                    st.session_state[session_key_ia] = res_ia if res_ia else fallback_phrase

            # 2. Bouton pour forcer la génération d'une nouvelle variante
            if st.button("🔄 Générer une autre variante pour ce niveau", key=f"btn_regen_variant_{combined_sig}"):
                with st.spinner("Création d'une nouvelle variante créative..."):
                    prompt_variant = (
                        f"Écris une *autre* courte dictée différente, parfaitement adaptée au niveau **{niveau_scolaire}**, "
                        f"qui intègre impérativement TOUS ces mots : {', '.join(words_list)}. "
                        f"Renvoie uniquement le texte brut."
                    )
                    res_var = interroger_ia(prompt_variant, temperature=0.8)
                    st.session_state[session_key_ia] = res_var if res_var else fallback_phrase
                    st.rerun()

            # Récupération de la phrase générée
            phrase_base = st.session_state.get(session_key_ia, fallback_phrase)
            
            # --- Application DYS sécurisée sur la phrase générée ---
            words_in_phrase = phrase_base.split() if phrase_base else ["Erreur", "de", "génération"]
            dys_phrase_parts = []
            
            for token in words_in_phrase:
                try:
                    match = re.match(r"^(\W*)([\wàâäéèêëîïôöùûüçÑñæœ-]+)(\W*)$", token, re.IGNORECASE)
                    if match:
                        prefix, word_core, suffix = match.groups()
                        coded_word = render_word_multilevel(word_core, show_phonemes=False)
                        dys_phrase_parts.append(f"{prefix}{coded_word}{suffix}")
                    else:
                        dys_phrase_parts.append(token)
                except Exception:
                    dys_phrase_parts.append(token)
                    
            if not dys_phrase_parts:
                dys_phrase_parts = [phrase_base]
                
            phrase_base_dys = " ".join(dys_phrase_parts)
            
            # --- Version Élève : Création des trous sur les mots de la liste ---
            phrase_trous_dys = phrase_base_dys
            for w in words_list:
                w_clean = w.strip()
                if w_clean:
                    try:
                        coded_w = render_word_multilevel(w_clean, show_phonemes=False)
                        hole = "<span style='display: inline-block; min-width: 80px; border-bottom: 2px solid #000; margin: 0 4px;'>&nbsp;</span>"
                        phrase_trous_dys = re.sub(re.escape(coded_w), hole, phrase_trous_dys, flags=re.IGNORECASE)
                        phrase_trous_dys = re.sub(r'\b' + re.escape(w_clean) + r'\b', hole, phrase_trous_dys, flags=re.IGNORECASE)
                    except Exception:
                        pass
                
            st.markdown("#### 📝 Version Élève (À trous avec Code Couleur DYS)")
            st.markdown(f"<div style='background-color: #ffffff; padding: 25px; border: 1px solid #ddd; border-radius: 10px; font-size: 22px; line-height: 2.2; color: #000000;'>{phrase_trous_dys}</div>", unsafe_allow_html=True)
            
            p4_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 4 - Exercice</title></head><body style='font-family: sans-serif; padding: 40px; font-size: 22px; line-height: 2.5; color: #000000;'><h1 style='text-align: center;'>Dictée en contexte ({niveau_scolaire}) - Exercice</h1><hr><br><div style='padding: 20px;'>{phrase_trous_dys}</div></body></html>"
            st.download_button("📥 Télécharger / Imprimer la Fiche Élève (HTML)", data=p4_export, file_name=f"page4_eleve_{niveau_scolaire}_{file_signature}.html", mime="text/html", key=f"dl_p4_eleve_{file_signature}")

            st.markdown("---")
            
            # --- Version Correcteur ---
            st.markdown("#### ✅ Version Correcteur (Texte Complet DYS)")
            st.markdown(f"<div style='background-color: #f8fafc; padding: 25px; border: 1px dashed #4f46e5; border-radius: 10px; font-size: 22px; line-height: 2.2; color: #000000;'>{phrase_base_dys}</div>", unsafe_allow_html=True)
            
            p4_corr_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Page 4 - Corrigé</title></head><body style='font-family: sans-serif; padding: 40px; font-size: 22px; line-height: 2.5; color: #000000;'><h1 style='text-align: center;'>Corrigé - Dictée en contexte ({niveau_scolaire})</h1><hr><br><div style='padding: 20px;'>{phrase_base_dys}</div></body></html>"
            st.download_button("📥 Télécharger / Imprimer le Corrigé (HTML)", data=p4_corr_export, file_name=f"page4_corrige_{niveau_scolaire}_{file_signature}.html", mime="text/html", key=f"dl_p4_corr_{file_signature}")
            
