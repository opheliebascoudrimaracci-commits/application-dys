import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random
import hashlib
import json
from openai import OpenAI
import google.generativeai as genai

# ==========================================
# UTILITAIRE IA CENTRALISÉ (Groq / Gemini)
# ==========================================
def interroger_ia(prompt_texte, temperature=0.8):
    """
    Fonction centralisée avec liste de modèles Groq étendue 
    (noms courts + noms avec préfixe organisation) et fallback Gemini.
    """
    erreurs = []

    # 1. TENTATIVE AVEC GROQ (SDK OpenAI standard)
    groq_key = st.secrets.get("GROQ_API_KEY")
    if groq_key:
        try:
            client = OpenAI(
                api_key=groq_key.strip(),
                base_url="https://api.groq.com/openai/v1",
            )
            # Liste complète des identifiants (formats récents et classiques)
            groq_models = [
                "llama-3.1-8b-instant",
                "openai/gpt-oss-20b",
                "llama-3.3-70b-versatile",
                "mixtral-8x7b-32768",
                "gpt-oss-20b"
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

    # 2. SECOURS AUTOMATIQUE AVEC GOOGLE GEMINI
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key.strip())
            model = genai.GenerativeModel("gemini-3.8-flash")
            res = model.generate_content(prompt_texte, generation_config={"temperature": temperature})
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            erreurs.append(f"Gemini: {e}")
    else:
        erreurs.append("Gemini: Clé 'GEMINI_API_KEY' absente des secrets")

    return f"Erreur IA -> " + " | ".join(erreurs)

    # 1. TENTATIVE AVEC GROQ
    groq_key = st.secrets.get("GROQ_API_KEY")
    if groq_key:
        try:
            client = OpenAI(
                api_key=groq_key.strip(),
                base_url="https://api.groq.com/openai/v1",
            )
            # Modèles actifs sur Groq
            groq_models = [
                "gpt-oss-20b",
                "llama-3.3-70b-versatile",
                "gpt-oss-120b"
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

    # 2. SECOURS AUTOMATIQUE AVEC GOOGLE GEMINI
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key.strip())
            model = genai.GenerativeModel("gemini-3.8-flash")
            res = model.generate_content(prompt_texte, generation_config={"temperature": temperature})
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            erreurs.append(f"Gemini: {e}")
    else:
        erreurs.append("Gemini: Clé 'GEMINI_API_KEY' absente des secrets")

    return f"Erreur IA -> " + " | ".join(erreurs)
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

def count_syllables_approx(word):
    w_clean = word.strip().lower()
    if 'syllables_cache' in st.session_state:
        return st.session_state['syllables_cache'].get(w_clean, max(1, len(w_clean) // 3))
    return max(1, len(w_clean) // 3)

def parse_word_to_blocks(word, is_plural_verb=False, keep_final_consonant=False):
    blocks = []
    w_lower = word.lower()
    n = len(word)
    i = 0
    
    while i < n:
        char = word[i]
        c_lower = w_lower[i]
        
        # Gestion du "th" (le t se prononce, le h est grisé)
        if i < n - 1 and w_lower[i:i+2] == 'th':
            blocks.append({'text': word[i], 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': 't'})
            blocks.append({'text': word[i+1], 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 2
            continue

        # Gestion du 's' final (prenant en compte keep_final_consonant pour Mathis, etc.)
        if c_lower == 's':
            is_prev_vowel = (i > 0 and word[i-1].lower() in ['a', 'e', 'i', 'o', 'u', 'y'])
            is_next_vowel = (i + 1 < n and word[i+1].lower() in ['a', 'e', 'i', 'o', 'u', 'y'])
            is_final = (i == n - 1)
            
            if is_prev_vowel and is_next_vowel:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': '#0d9488', 'phoneme': 'z'})
            elif is_final and not keep_final_consonant:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue

        # Autres consonnes finales (t, d, x)
        if i == n - 1 and c_lower in ['t', 'd', 'x'] and n > 2:
            if keep_final_consonant:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 1
            continue

        # Caractère par défaut
        blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
        i += 1
        
    return blocks

# Liste des prénoms dont la consonne finale (s, x, etc.) se prononce en français
PRENOMS_CONSONNE_FINALE_PRONONCEE = ["mathis", "alexis", "loic", "loïc", "yanis", "iris", "jervis"]

def render_word_multilevel(word, show_phonemes=True, prev_word="", show_arcs=True):
    clean_word_lower = word.lower().strip()
    
    # On vérifie si c'est un prénom à consonne finale prononcée
    is_consonne_prononcee = clean_word_lower in PRENOMS_CONSONNE_FINALE_PRONONCEE
        
    clean_prev = prev_word.strip().lower() if prev_word else ""
    clean_word = word.strip().lower()
    
    is_plural_verb = (clean_prev in PLURAL_SUBJECTS) and clean_word.endswith("ent") and len(clean_word) > 4
    
    # On transmet l'information au parseur
    blocks = parse_word_to_blocks(word, is_plural_verb=is_plural_verb, keep_final_consonant=is_consonne_prononcee)
    
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
    
    style_bg = (
        "background-color: #f4f6f9; "
        "padding: 15px; "
        "border-radius: 8px; "
        "border-left: 5px solid #4a90e2; "
        "color: #111111;"
    ) if soft_bg else ""
    
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
                extracted_text = pytesseract.image_to_string(img, lang='fra')
                if extracted_text.strip():
                    st.success("Texte extrait avec succès !")
                    opts = build_controls("ocr_ctrl")
                    render_full_dys_text(extracted_text, **opts)
                else:
                    st.warning("Aucun texte n'a pu être extrait de cette image.")
            except Exception as e:
                st.error(f"Erreur OCR : {e}")

elif menu_selection == "✨ Générateur d'histoires":
    st.title("✨ Générateur d'histoires d'apprentissage")
    st.subheader("Ophélie Bascou Drimaracci")
    
    theme = st.text_input("Thème de l'histoire (ex: Un petit dragon courageux) :")
    niveau = st.selectbox("Niveau scolaire :", ["CP", "CE1", "CE2", "CM1", "CM2"])
    
    if st.button("🪄 Générer l'histoire") and theme:
        with st.spinner("L'IA invente une histoire..."):
            prompt = f"Écris une courte histoire captivante pour un enfant de niveau {niveau} sur le thème : '{theme}'. Texte simple, positif, environ 100 mots."
            histoire = interroger_ia(prompt, temperature=0.8)
            st.session_state["histoire_generee"] = histoire

    if "histoire_generee" in st.session_state:
        st.write("---")
        opts = build_controls("histoire_gen")
        render_full_dys_text(st.session_state["histoire_generee"], **opts)

elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.caption("Ophélie Bascou Drimaracci")
    st.write("Saisissez vos mots. L'IA analyse instantanément la phonétique et génère les 4 pages de travail adaptées !")

    mots_input = st.text_area("Entrez vos mots (séparés par un espace, une virgule ou une ligne) :", "Poulet, lampe, chat", height=100)
    
    words_list = [w.strip() for w in re.split(r'[\n,\s]+', mots_input) if w.strip()]
    file_signature = hashlib.md5(",".join(words_list).encode('utf-8')).hexdigest()[:8]

    if words_list:
        st.success(f"📋 {len(words_list)} mot(s) actif(s) : {', '.join(words_list)}")

        dic_tab1, dic_tab2, dic_tab3, dic_tab4 = st.tabs([
            "Page 1 : 🎨 Mots codés DYS",
            "Page 2 : ✂️ Mots découpés",
            "Page 3 : ✏️ Mots à trous",
            "Page 4 : 📝 Phrase contextuelle (IA)"
        ])

        with dic_tab1:
            st.markdown("### Page 1 : Mots de la dictée avec codage couleur DYS")
            for w in words_list:
                st.markdown(render_word_multilevel(w), unsafe_allow_html=True)

        with dic_tab2:
            st.markdown("### Page 2 : Mots découpés par syllabes")
            for w in words_list:
                num_syll = count_syllables_approx(w)
                st.write(f"**{w}** ({num_syll} syllabes)")

        with dic_tab3:
            st.markdown("### Page 3 : Mots à trous pour entraînement")
            for w in words_list:
                st.write(f"{w[0]} _ _ _ {w[-1] if len(w) > 1 else ''}")

        # -------------------------------------------------------------
        # PAGE 4 : Dictée en contexte (IA : Groq en priorité + Gemini en secours)
        # -------------------------------------------------------------
        with dic_tab4:
            st.markdown("### Page 4 : Phrase de dictée en contexte (Générée par l'IA)")
            
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
                index=2,
                key=f"select_niveau_{file_signature}"
            )
            
            combined_sig = f"{file_signature}_{niveau_scolaire}"
            session_key_ia = f"phrase_ia_{combined_sig}"
            fallback_phrase = f"Aujourd'hui, nous étudions avec attention les mots suivants : {', '.join(words_list)}."

            prompt_phrase = (
                f"Tu es un professeur expert en pédagogie et élèves DYS. "
                f"Écris une courte dictée originale, claire et parfaitement adaptée au niveau scolaire : **{niveau_scolaire}**. "
                f"Le texte doit intégrer impérativement et naturellement TOUS ces mots : {', '.join(words_list)}. "
                f"Renvoie uniquement le texte de la dictée, sans aucune introduction, sans guillemets et sans commentaires."
            )

            if session_key_ia not in st.session_state:
                with st.spinner(f"🤖 L'IA compose une dictée unique pour le niveau {niveau_scolaire}..."):
                    res_ia = interroger_ia(prompt_phrase, temperature=0.8)
                    st.session_state[session_key_ia] = res_ia if res_ia else fallback_phrase

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
            
            p4_corr_export = f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'><title>Corrigé Page 4</title></head><body style='font-family: sans-serif; padding: 40px; font-size: 22px; line-height: 2.5; color: #000000;'><h1 style='text-align: center;'>Corrigé - Dictée en contexte ({niveau_scolaire})</h1><hr><br><div style='padding: 20px;'>{phrase_base_dys}</div></body></html>"
            st.download_button("📥 Télécharger / Imprimer le Corrigé (HTML)", data=p4_corr_export, file_name=f"page4_corrige_{niveau_scolaire}_{file_signature}.html", mime="text/html", key=f"dl_p4_corr_{file_signature}")
