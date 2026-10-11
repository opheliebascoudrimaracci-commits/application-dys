import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random
import hashlib
import json
import google.generativeai as genai

# Configuration de la clé (via les secrets Streamlit Cloud)
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
        "🎤 Aide à la dictée"
    ]
)

PLURAL_SUBJECTS = {
    "ils", "elles", "les", "des", "ces", "mes", "tes", "ses", "nos", "vos", "leurs",
    "deux", "trois", "quatre", "cinq", "plusieurs", "certains", "certaines"
}

# ---------------------------------------------------------
# ANALYSE INTELLIGENTE PAR L'IA (Syllabes, Blocs & Phonèmes)
# ---------------------------------------------------------

def analyze_word_with_ai(word):
    """Interroge Gemini pour obtenir le découpage pédagogique complet d'un mot (syllabes, blocs de couleurs, phonèmes, lettres muettes)."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
Analyse ce mot français pour un élève dysléxique : '{word}'.
Renvoie STRICTEMENT un objet JSON valide (sans markdown autour, sans texte explicatif) avec cette structure exacte :
{{
  "syllables_count": <nombre entier de syllabes orales>,
  "blocks": [
    {{
      "text": "<segment ou lettre du mot>",
      "render_type": "<'normal' ou 'highlight' ou 'muted' ou 'color_text'>",
      "color": "<code hexadécimal de couleur si coloré ou mis en valeur, ex: #8E44AD, ou null>",
      "phoneme": "<phonème simplifié associé en phonétique si pertinent, ex: 'è', 'j', 'k', ou null>"
    }}
  ]
}}
Règles pédagogiques :
- Les lettres muettes (comme le 'h' dans Mathis, le 'e' final muet, le 's' muet) doivent avoir "render_type": "muted" et une couleur grise ou null.
- Les sons complexes (ou, an, in, ch, ge [j], qu [k], etc.) doivent être regroupés dans un même bloc avec "render_type": "highlight" et une couleur spécifique.
- Le découpage combiné de tous les blocs de texte doit reformer exactement le mot d'origine.
"""
        model = genai.GenerativeModel("gemini-2.5-flash")
        res = model.generate_content(prompt)
        
        if res and res.text:
            cleaned_text = res.text.strip()
            # Nettoyage au cas où l'IA ajoute des balises markdown de code
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            data = json.loads(cleaned_text)
            if "blocks" in data and "syllables_count" in data:
                return data
    except Exception:
        pass
    
    # Mode secours par défaut si l'IA échoue
    return {
        "syllables_count": max(1, len(word) // 3),
        "blocks": [{"text": char, "render_type": "normal", "color": None, "phoneme": None} for char in word]
    }

# Initialisation du cache global des mots analysés par l'IA
if 'words_list' in locals() and words_list:
    if 'file_signature' not in locals():
        file_signature = "_".join([w.strip() for w in words_list])

    if 'word_analysis_cache' not in st.session_state or st.session_state.get('sig_analysis') != file_signature:
        st.session_state['sig_analysis'] = file_signature
        st.session_state['word_analysis_cache'] = {}
        for w in words_list:
            w_clean = w.strip().lower()
            if w_clean:
                st.session_state['word_analysis_cache'][w_clean] = analyze_word_with_ai(w_clean)

def get_word_syllables(word):
    w_clean = word.strip().lower()
    if 'word_analysis_cache' in st.session_state and w_clean in st.session_state['word_analysis_cache']:
        return st.session_state['word_analysis_cache'][w_clean].get("syllables_count", 1)
    return max(1, len(word) // 3)

def parse_word_to_blocks(word, is_plural_verb=False):
    w_clean = word.strip().lower()
    # Si le mot est en cache, on renvoie l'analyse IA
    if 'word_analysis_cache' in st.session_state and w_clean in st.session_state['word_analysis_cache']:
        return st.session_state['word_analysis_cache'][w_clean].get("blocks", [])
    
    # Analyse à la volée si le mot n'est pas dans le cache principal
    analysis = analyze_word_with_ai(w_clean)
    return analysis.get("blocks", [{"text": char, "render_type": "normal", "color": None, "phoneme": None} for char in word])


def render_word_multilevel(word, show_phonemes=True, prev_word="", show_arcs=True):
    clean_word = word.strip()
    if not clean_word:
        return ""
        
    clean_prev = prev_word.strip().lower() if prev_word else ""
    clean_word_lower = clean_word.lower()
    
    is_plural_verb = (clean_prev in PLURAL_SUBJECTS) and clean_word_lower.endswith("ent") and len(clean_word_lower) > 4
    blocks = parse_word_to_blocks(clean_word, is_plural_verb=is_plural_verb)
    
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block.get('text', '')
        color = block.get('color', '#000000') or '#000000'
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
            ph_color = color if color != '#000000' else '#555555'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-size: 0.75em;'>{phoneme}</span>")
        else:
            phoneme_html_parts.append(f"<span style='font-size: 0.75em;'>&nbsp;</span>")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""
    
    num_syllables = get_word_syllables(clean_word)
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
        placeholder="Exemple: Mathis, bateau, chant, magique",
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
        
        with dic_tab1:
            st.markdown("### Page 1 : Fiche de révision visuelle (IA)")
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
            
        with dic_tab2:
            st.markdown("### Page 2 : Mots découpés en syllabes et lettres")
            p2_parts = []
            
            for w in words_list:
                try:
                    letters_html = "".join([
                        f"<div style='display: inline-block; width: 35px; height: 35px; line-height: 35px; margin: 2px; border: 2px solid #1e1b4b; border-radius: 4px; text-align:
