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
import os

# ==========================================
# UTILITAIRE IA CENTRALISÉ (Groq / Gemini)
# ==========================================
def interroger_ia(prompt_texte, temperature=0.8):
    erreurs = []
    groq_key = st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            client = OpenAI(
                api_key=groq_key.strip(),
                base_url="https://api.groq.com/openai/v1",
            )
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
        erreurs.append("Groq: Clé 'GROQ_API_KEY' absente")

    gemini_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key.strip())
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt_texte, generation_config={"temperature": temperature})
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            erreurs.append(f"Gemini: {e}")
    else:
        erreurs.append("Gemini: Clé 'GEMINI_API_KEY' absente")
    return f"Erreur IA -> " + " | ".join(erreurs)

# --- MENU LATÉRAL PRINCIPAL ---
st.sidebar.title("📌 Navigation")
menu_selection = st.sidebar.radio(
    "Choisissez un module :",
    [
        "🏠 Présentation",
        "📄 Aide à la lecture (Texte & OCR)",
        "✨ Générateur d'histoires",
        "🎤 Aide à la dictée",
        "📐 Grammaire Visuelle & Accords"
    ]
)

PLURAL_SUBJECTS = {
    "ils", "elles", "les", "des", "ces", "mes", "tes", "ses", "nos", "vos", "leurs",
    "deux", "trois", "quatre", "cinq", "plusieurs", "certains", "certaines"
}

# Dictionnaire des sons complexes (Code couleur de référence)
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
    'el': ('#333333', 'l'),
}

PRENOMS_CONSONNE_FINALE_PRONONCEE = {"mathis", "iris", "lucas", "yanis", "alix", "félix", "david"}
VOWELS = "aeiouyàâäéèêëïîôöùûüÿ"

@st.cache_data
def analyser_syllabes_texte_ia_v3(texte):
    decoupages_fixes = {
        "bonjour": "bon-jour",
        "banane": "ba-na-ne",
        "j'aime": "j'ai-me",
        "ecole": "é-co-le",
        "vacances": "va-can-ces",
        "voiture": "voi-ture",
        "maison": "mai-son",
        "appelle": "ap-pel-le",
        "m'appelle": "m'ap-pel-le",
        "connaissais": "con-nais-sais",
        "parti": "par-ti"
    }
    
    words = list(set(texte.lower().strip().split()))
    words_clean = [w.strip(".,;:?!'\"«»' ") for w in words if len(w.strip(".,;:?!'\"«»' ")) > 0]
    
    syllables_map = {}
    mots_a_analyser = []
    
    for w in words_clean:
        if w in decoupages_fixes:
            syllables_map[w] = decoupages_fixes[w]
        else:
            mots_a_analyser.append(w)
            
    if mots_a_analyser:
        prompt = f"""
Pour chacun des mots suivants en français, réécris le mot en séparant ses syllabes orales par un tiret (-).
Réponds UNIQUEMENT sous la forme "mot:mo-t-de-cou-pé", un par ligne. Exemple :
maison:mai-son
Mots à analyser :
{", ".join(mots_a_analyser)}
"""
        try:
            reponse = interroger_ia(prompt, temperature=0.0).strip()
            for ligne in reponse.split("\n"):
                if ":" in ligne:
                    parts = ligne.split(":")
                    mot = parts[0].strip().lower()
                    decoupe = parts[1].strip()
                    syllables_map[mot] = decoupe
        except Exception:
            pass
            
    for w in words_clean:
        if w not in syllables_map or "-" not in syllables_map[w]:
            syllables_map[w] = w
            
    return syllables_map

def count_syllables_approx(word):
    clean_w = word.lower().strip(".,;:?!'\"«»' ")
    if not clean_w:
        return 1
    vowels = "aeiouyàâäéèêëïîôöùûüÿ"
    if clean_w.endswith('e') and len(clean_w) > 3 and not clean_w.endswith(('ée', 'ie', 'ue', 'oe')):
        clean_w = clean_w[:-1]
    count = 0
    in_vowel_group = False
    for char in clean_w:
        if char in vowels:
            if not in_vowel_group:
                count += 1
                in_vowel_group = True
        else:
            in_vowel_group = False
    return max(1, count)

def parse_word_to_blocks(word, sounds_dict=None, is_plural_verb=False, keep_final_consonant=False, is_end_of_sentence=False):
    blocks = []
    clean_word = word.strip(".,;:?!'\"«» ")
    w_lower = clean_word.lower()
    n = len(word)
    i = 0
    VOWELS = "aeiouyàâäéèêëîïôöùûüÿœæ"
    
    if w_lower == "et":
        if is_end_of_sentence:
            for char in word:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            return blocks
        else:
            blocks.append({'text': word, 'is_muted': False, 'render_type': 'color_text', 'color': '#8E44AD', 'phoneme': 'é'})
            return blocks
            
    if not sounds_dict:
        sounds_dict = EXACT_COMPLEX_SOUNDS
        
    while i < n:
        char = word[i]
        c_lower = char.lower()
        if i == n - 2 and w_lower[i:i+2] == 'et' and n > 2:
            blocks.append({'text': word[i:i+2], 'is_muted': False, 'render_type': 'color_text', 'color': '#8E44AD', 'phoneme': 'é'})
            i += 2
            continue
        if i < n - 1 and w_lower[i:i+2] == 'th':
            blocks.append({'text': word[i], 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': 't'})
            blocks.append({'text': word[i+1], 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 2
            continue
            
        special_sounds = {
            'eau': ('#D35400', 'o'), 'ch': ('#2980B9', 'ʃ'), 'ph': ('#8E44AD', 'f'),
            'ou': ('#D35400', 'u'), 'on': ('#16A085', 'ɔ̃'), 'an': ('#27AE60', 'ɑ̃'),
            'en': ('#27AE60', 'ɑ̃'), 'in': ('#8E44AD', 'ɛ̃'), 'un': ('#8E44AD', 'œ̃'),
            'oi': ('#C0392B', 'wa'), 'gn': ('#7F8C8D', 'ɲ'), 'ui': ('#2980B9', 'ɥi'),
            'eu': ('#D35400', 'ø'), 'au': ('#D35400', 'o')
        }
        
        matched_special = False
        if i + 3 <= n and w_lower[i:i+3] in special_sounds:
            sub3 = w_lower[i:i+3]
            color, phoneme = special_sounds[sub3]
            blocks.append({'text': word[i:i+3], 'is_muted': False, 'render_type': 'color_text', 'color': color, 'phoneme': phoneme})
            i += 3
            continue
        if i + 2 <= n and w_lower[i:i+2] in special_sounds:
            sub2 = w_lower[i:i+2]
            color, phoneme = special_sounds[sub2]
            blocks.append({'text': word[i:i+2], 'is_muted': False, 'render_type': 'color_text', 'color': color, 'phoneme': phoneme})
            i += 2
            continue
            
        matched_complex = False
        if sounds_dict:
            for length in [4, 3, 2]:
                if i + length <= n:
                    sub = w_lower[i:i+length]
                    if sub in sounds_dict:
                        rule = sounds_dict[sub]
                        blocks.append({'text': word[i:i+length], 'is_muted': False, 'render_type': 'color_text', 'color': rule[0], 'phoneme': rule[1]})
                        i += length
                        matched_complex = True
                        break
        if matched_complex:
            continue
            
        if is_plural_verb and i >= n - 3:
            blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 1
            continue
        if c_lower == 's':
            is_prev_vowel = (i > 0 and word[i-1].lower() in VOWELS)
            is_next_vowel = (i + 1 < n and word[i+1].lower() in VOWELS)
            is_final = (i == n - 1)
            if is_prev_vowel and is_next_vowel:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'color_text', 'color': '#0d9488', 'phoneme': 'z'})
            elif is_final and not keep_final_consonant:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            i += 1
            continue
        if i == n - 1 and c_lower in ['t', 'd', 'x'] and n > 2:
            if keep_final_consonant:
                blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
            else:
                blocks.append({'text': char, 'is_muted': True, 'render_type': 'muted', 'color': None, 'phoneme': None})
            i += 1
            continue
            
        blocks.append({'text': char, 'is_muted': False, 'render_type': 'normal', 'color': None, 'phoneme': None})
        i += 1
    return blocks

def render_word_multilevel(word, show_phonemes=True, show_colors=True, show_arcs=True, prev_word="", is_end_of_sentence=False, nb_syllables_override=None):
    clean_word_lower = word.lower().strip(".,;:?!'\"«» ")
    prenoms_exclus = PRENOMS_CONSONNE_FINALE_PRONONCEE
    is_consonne_prononcee = clean_word_lower in prenoms_exclus
    clean_prev = prev_word.strip().lower() if prev_word else ""
    clean_word = word.strip().lower()
    is_plural_verb = (clean_prev in PLURAL_SUBJECTS) and clean_word.endswith("ent") and len(clean_word) > 4
    
    blocks = parse_word_to_blocks(
        word, 
        is_plural_verb=is_plural_verb, 
        keep_final_consonant=is_consonne_prononcee,
        is_end_of_sentence=is_end_of_sentence
    )
    
    word_html_parts = []
    phoneme_html_parts = []
    
    for block in blocks:
        text = block.get('text', '')
        color = block.get('color', '#000000')
        phoneme = block.get('phoneme', '')
        render_type = block.get('render_type', 'normal')
        
        if show_colors:
            if render_type == 'highlight':
                txt_styled = f"<span style='color: {color}; font-weight: bold;'>{text}</span>"
            elif render_type == 'color_text':
                txt_styled = f"<span style='color: {color};'>{text}</span>"
            elif render_type == 'muted':
                txt_styled = f"<span style='color: #a0a0a0; text-decoration: line-through;'>{text}</span>"
            else:
                txt_styled = f"<span>{text}</span>"
        else:
            if render_type == 'muted':
                txt_styled = f"<span style='color: #a0a0a0; text-decoration: line-through;'>{text}</span>"
            else:
                txt_styled = f"<span>{text}</span>"
                
        word_html_parts.append(f"<span>{txt_styled}</span>")
        if show_phonemes and phoneme:
            ph_color = color if show_colors and color else '#555555'
            phoneme_html_parts.append(f"<span style='color: {ph_color}; font-size: 0.75em;'>{phoneme}</span>")
        else:
            phoneme_html_parts.append(f"<span style='font-size: 0.75em;'>&nbsp;</span>")
            
    w_main = "".join(word_html_parts)
    w_ph = " ".join(phoneme_html_parts) if show_phonemes else ""
    
    if nb_syllables_override is not None:
        if isinstance(nb_syllables_override, str):
            num_syllables = max(1, len(nb_syllables_override.split('-')))
        else:
            num_syllables = max(1, nb_syllables_override)
    else:
        num_syllables = count_syllables_approx(word)
        
    if show_arcs:
        arcs_html = "".join([
            "<span style='display: inline-block; width: 16px; height: 7px; border: 2px solid #4a90e2; border-top: none; border-radius: 0 0 12px 12px; margin: 0 2px;'></span>" 
            for _ in range(num_syllables)
        ])
        w_arcs = f"<div style='line-height: 0; margin-top: 4px; text-align: center;'>{arcs_html}</div>"
    else:
        w_arcs = ""
        
    html = f"<span style='display: inline-block; text-align: center; margin: 0 6px; vertical-align: top;'>"
    html += f"<div>{w_main}</div>"
    if show_arcs:
        html += w_arcs
    if show_phonemes:
        html += f"<div style='font-size: 0.8em; margin-top: 4px; text-align: center;'>{w_ph}</div>"
    html += "</span>"
    return html

def render_full_dys_text(text, show_phonemes=True, show_colors=True, show_arcs=True, word_alt=False, line_alt=False, size=18, soft_bg=True, key_suffix="", **kwargs):
    syllables_map = analyser_syllabes_texte_ia_v3(text) if show_arcs else {}
    lines = text.split('\n')
    rendered_lines_adapted = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        for idx, word in enumerate(words):
            prev_word = words[idx - 1] if idx > 0 else ""
            clean_w = word.lower().strip(".,;:?!'\"«»' ")
            decoupe_ia = syllables_map.get(clean_w, word)
            word_html = render_word_multilevel(
                word, 
                show_phonemes=show_phonemes, 
                show_colors=show_colors, 
                show_arcs=show_arcs, 
                prev_word=prev_word,
                nb_syllables_override=decoupe_ia
            )
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
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2; color: #111111;" if soft_bg else ""
    
    st.markdown("### 👁️ Aperçu adapté :")
    st.markdown(f"<div style='font-size: {size}px; {style_bg}'>{full_content_adapted}</div>", unsafe_allow_html=True)

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

def format_to_str(content):
    if isinstance(content, list):
        return "\n".join([format_to_str(item) for item in content])
    elif isinstance(content, dict):
        return "\n".join([f"{k}: {format_to_str(v)}" for k, v in content.items()])
    return str(content)

def charger_historique():
    if "historique_phrases" not in st.session_state:
        st.session_state["historique_phrases"] = [
            {
                "niveau": 1,
                "texte": "Le petit chat noir dort sur le tapis.",
                "mots": [
                    {"mot": "Le", "type": "determinant"},
                    {"mot": "petit", "type": "adjectif"},
                    {"mot": "chat", "type": "nom"},
                    {"mot": "noir", "type": "adjectif"},
                    {"mot": "dort", "type": "verbe"},
                    {"mot": "sur", "type": "invariable"},
                    {"mot": "le", "type": "determinant"},
                    {"mot": "tapis", "type": "nom"}
                ],
                "accord": {
                    "phrase_trou": "Le petit chat noir dor__ sur le tapis.",
                    "options": ["rien", "s", "t", "nt"],
                    "reponse": "t"
                }
            }
        ]
    return st.session_state["historique_phrases"]

def sauvegarder_phrase_dans_historique(phrase):
    if "historique_phrases" not in st.session_state:
        st.session_state["historique_phrases"] = []
    if phrase and phrase not in st.session_state["historique_phrases"]:
        st.session_state["historique_phrases"].append(phrase)

def afficher_legende_couleurs():
    st.sidebar.markdown("### 🏷️ Légende des symboles")
    st.sidebar.markdown("- 🔺 Déterminants")
    st.sidebar.markdown("- 💖 Pronoms")
    st.sidebar.markdown("- ⭐ / ✨ Noms")
    st.sidebar.markdown("- 🟩 Verbes")
    st.sidebar.markdown("- ⬛ Invariables")
    st.sidebar.markdown("- 🔵 Adjectifs")

SYMBOLES_GRAMMAIRE = {
    "determinant": {"label": "Déterminant", "emoji": "🔺", "couleur": "#e74c3c"},
    "det": {"label": "Déterminant", "emoji": "🔺", "couleur": "#e74c3c"},
    "pronom": {"label": "Pronom", "emoji": "💖", "couleur": "#9b59b6"},
    "pron": {"label": "Pronom", "emoji": "💖", "couleur": "#9b59b6"},
    "nom": {"label": "Nom commun", "emoji": "⭐", "couleur": "#f1c40f"},
    "nom_commun": {"label": "Nom commun", "emoji": "⭐", "couleur": "#f1c40f"},
    "nom_propre": {"label": "Nom propre", "emoji": "✨", "couleur": "#f1c40f"},
    "verbe": {"label": "Verbe", "emoji": "🟩", "couleur": "#2ecc71"},
    "v": {"label": "Verbe", "emoji": "🟩", "couleur": "#2ecc71"},
    "invariable": {"label": "Mot invariable", "emoji": "⬛", "couleur": "#34495e"},
    "mot_invariable": {"label": "Mot invariable", "emoji": "⬛", "couleur": "#34495e"},
    "adjectif": {"label": "Adjectif", "emoji": "🔵", "couleur": "#3498db"},
    "adj": {"label": "Adjectif", "emoji": "🔵", "couleur": "#3498db"},
    "autre": {"label": "Autre", "emoji": "❓", "couleur": "#95a5a6"}
}

def afficher_phrase_symboles(phrase_data):
    mots = phrase_data.get("mots", [])
    if not mots:
        st.warning("Aucune phrase à afficher.")
        return
    html_mots = []
    for m in mots:
        type_mot = m.get("type", "").lower()
        info_symb = SYMBOLES_GRAMMAIRE.get(type_mot, {"emoji": "❓", "label": "Autre"})
        emoji_display = info_symb.get("emoji", "❓")
        mot_texte = m.get('mot', '')
        html_mots.append(
            f"<div style='display:inline-block; text-align:center; margin:8px 10px; padding:10px 12px; background:#ffffff; border-radius:8px; border:1px solid #dcdde1; vertical-align:top;'>"
            f"<div style='font-size:22px; font-weight:bold; color:#2c3e50; margin-bottom:6px;'>{mot_texte}</div>"
            f"<div style='font-size:20px;'>{emoji_display}</div>"
            f"<div style='font-size:8pt; color:#666;'>{info_symb.get('label','')}</div>"
            f"</div>"
        )
    st.markdown(f"<div style='text-align:center; background:#f8f9fa; padding:15px; border-radius:12px; border:1px solid #e1e8ed;'>{''.join(html_mots)}</div>", unsafe_allow_html=True)

def generer_ou_analyser_phrase_ia(fonction_appel_ia, texte_force=None, niveau=1):
    if texte_force:
        mots_bruts = texte_force.split()
        mots_list = [{"mot": m, "type": "nom" if i%2==0 else "determinant"} for i, m in enumerate(mots_bruts)]
        return {
            "texte": texte_force,
            "niveau": niveau,
            "mots": mots_list,
            "accord": {
                "phrase_trou": texte_force,
                "options": ["s", "e", "ent", "rien"],
                "reponse": "rien"
            }
        }
    return {
        "texte": "Les enfants jouent dans la cour.",
        "niveau": niveau,
        "mots": [
            {"mot": "Les", "type": "determinant"},
            {"mot": "enfants", "type": "nom"},
            {"mot": "jouent", "type": "verbe"},
            {"mot": "dans", "type": "invariable"},
            {"mot": "la", "type": "determinant"},
            {"mot": "cour", "type": "nom"}
        ],
        "accord": {
            "phrase_trou": "Les enfant__ jouent dans la cour.",
            "options": ["s", "x", "rien"],
            "reponse": "s"
        }
    }

def generer_fiche_html_imprimable(phrase):
    mots = phrase.get("mots", [])
    accord = phrase.get("accord", {})
    mots_html = ""
    for m in mots:
        mots_html += f"""
        <div style="text-align: center; border: 1px solid #ddd; padding: 4px; border-radius: 4px; min-width: 50px; background: #fdfdfd;">
            <div style="font-size: 9pt; color: #666; margin-bottom: 2px;">{m.get('type', '')}</div>
            <div style="font-weight: bold; font-size: 11pt;">{m.get('mot', '')}</div>
        </div>
        """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4 portrait; margin: 8mm; }}
            body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #2c3e50; line-height: 1.25; margin: 0; padding: 0; }}
            .header {{ text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 4px; margin-bottom: 10px; }}
            .header h1 {{ font-size: 13pt; margin: 0 0 3px 0; color: #2c3e50; }}
            .section {{ border: 1px solid #bdc3c7; border-radius: 4px; padding: 6px 10px; margin-bottom: 8px; background-color: #fafafa; }}
            .section-title {{ font-weight: bold; color: #2980b9; font-size: 10pt; margin-bottom: 5px; border-bottom: 1px dashed #ddd; padding-bottom: 2px; }}
            .mots-container {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 5px; }}
            .footer {{ text-align: center; font-size: 8pt; color: #888; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Fiche Mémo & Exercices : Grammaire Visuelle</h1>
            <p>Niveau {phrase.get('niveau', 1)} | Application Pédagogique DYS</p>
        </div>
        <div class="section">
            <div class="section-title">1. Découverte & Analyse de la phrase</div>
            <p style="text-align: center; font-size: 11pt; font-weight: bold; margin: 5px 0;">"{phrase.get('texte', '')}"</p>
            <div class="mots-container">{mots_html}</div>
        </div>
        <div class="section">
            <div class="section-title">2. Exercice : Associer chaque mot à sa nature</div>
        </div>
        <div class="section">
            <div class="section-title">3. Exercice d'Accords</div>
            <p style="margin: 4px 0;"><b>Phrase à compléter :</b> {accord.get('phrase_trou', phrase.get('texte', ''))}</p>
        </div>
        <div class="footer">Document généré pour un usage pédagogique individualisé.</div>
    </body>
    </html>
    return html_content

def afficher_page_grammaire(fonction_appel_ia):
    st.header("📐 Module Grammaire Visuelle & Accords")
    
    mode_choix = st.radio(
        "Source de la phrase :",
        ["Piocher dans la banque de 100 phrases", "Écrire ma propre phrase", "Générer une phrase inédite avec l'IA"],
        horizontal=True,
        key="mode_grammaire_radio"
    )

    historique = charger_historique()

    if mode_choix == "Piocher dans la banque de 100 phrases":
        niveau_sel = st.selectbox("Sélectionner le niveau :", [1, 2, 3], format_func=lambda x: f"Niveau {x}", key="niv_sel_gram")
        phrases_dispos = [p for p in historique if p.get("niveau") == niveau_sel]
        if phrases_dispos:
            st.session_state.phrase_grammaire = random.choice(phrases_dispos)
        else:
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=niveau_sel)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    elif mode_choix == "Écrire ma propre phrase":
        saisie_user = st.text_input("Saisissez votre phrase :", key="input_saisie_libre")
        if st.button("Analyser et ajouter à la banque", key="btn_analyse_libre"):
            if saisie_user.strip():
                with st.spinner("Analyse et découpage en cours..."):
                    nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, texte_force=saisie_user)
                    if not isinstance(nouvelle, dict) or "mots" not in nouvelle:
                        mots_decoupes = [{"mot": m, "type": "autre"} for m in saisie_user.split()]
                        nouvelle = {
                            "texte": saisie_user,
                            "niveau": 1,
                            "mots": mots_decoupes,
                            "accord": {"phrase_trou": saisie_user, "options": ["s", "e", "ent"], "reponse": ""}
                        }
                sauvegarder_phrase_dans_historique(nouvelle)
                st.session_state.phrase_grammaire = nouvelle
                st.success("Phrase analysée et prête avec les symboles ! 🎉")
                st.rerun()
            else:
                st.warning("Veuillez entrer une phrase.")

    elif mode_choix == "Générer une phrase inédite avec l'IA":
        niveau_gen = st.selectbox("Niveau à générer :", ["CP", "CE1", "CE2"], key="select_niveau_gen")
        if st.button("Générer une nouvelle phrase", key="btn_gen_ia"):
            with st.spinner("Génération en cours..."):
                nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=1)
            if nouvelle:
                sauvegarder_phrase_dans_historique(nouvelle)
                st.session_state.phrase_grammaire = nouvelle
                st.success("Phrase générée et sauvegardée !")
                st.rerun()

    if "phrase_grammaire" not in st.session_state:
        if historique:
            st.session_state.phrase_grammaire = historique[0]
        else:
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=1)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    phrase = st.session_state.phrase_grammaire
    st.divider()

    tab_ex, tab_exo, tab_acc = st.tabs(["📖 Exemple", "✏️ Exercice (Symboles)", "✍️ Accords"])

    with tab_ex:
        st.subheader("Analyse de la phrase")
        afficher_legende_couleurs()
        afficher_phrase_symboles(phrase)

    with tab_exo:
        st.subheader("Identifie le symbole de chaque mot")
        with st.expander("ℹ️ Rappel du code couleur"):
            afficher_legende_couleurs()
        mots = phrase.get("mots", [])
        cols = st.columns(max(1, len(mots)))
        choix_eleve = {}
        for idx, m in enumerate(mots):
            with cols[idx]:
                st.markdown(f"<h4 style='text-align: center;'>{m['mot']}</h4>", unsafe_allow_html=True)
                choix_eleve[idx] = st.selectbox(
                    f"Symb {idx}",
                    ["-- Choisir --"] + [s["label"] for s in SYMBOLES_GRAMMAIRE.values()],
                    key=f"symb_sel_gram_{idx}",
                    label_visibility="collapsed"
                )
        if st.button("Valider mes symboles", key="valider_symb_gram"):
            exact = True
            for idx, m in enumerate(mots):
                label_attendu = SYMBOLES_GRAMMAIRE.get(m["type"], {}).get("label", "")
                if choix_eleve[idx] != label_attendu:
                    exact = False
            if exact:
                st.balloons()
                st.success("Bravo ! Tout est correct ! 🎉")
            else:
                st.warning("Il y a des erreurs, vérifie l'onglet Exemple.")

    with tab_acc:
        st.subheader("Exercice d'accord")
        accord = phrase.get("accord", {})
        st.markdown(f"### {accord.get('phrase_trou', phrase.get('texte', ''))}")
        choix_accord = st.radio(
            "Sélectionne la réponse correcte :",
            options=accord.get("options", ["Rien (pas d'accord)", "s", "e", "ent"]),
            horizontal=True,
            key="radio_accord_gram"
        )
        if st.button("Vérifier l'accord", key="btn_verif_accord"):
            if choix_accord == accord.get("reponse"):
                st.balloons()
                st.success("Excellente réponse ! 🌟")
            else:
                st.error(f"Attention, la bonne réponse était : '{accord.get('reponse')}'")

    st.divider()
    html_fiche = generer_fiche_html_imprimable(phrase)
    st.download_button(
        label="📥 Télécharger la fiche d'exercice",
        data=html_fiche,
        file_name=f"fiche_grammaire_niveau_{phrase.get('niveau', 1)}.html",
        mime="text/html",
        type="primary",
        key="download_fiche_gram"
)
# ==========================================
# GESTION DES PAGES DU MENU LATÉRAL
# ==========================================
elif menu_selection == "🏠 Présentation":
    st.title("✏️ Application Pédagogique & Adaptation DYS")
    st.subheader("Ophélie Bascou Drimaracci")
    st.write("---")
    st.write("Bienvenue sur cette application pédagogique conçue pour faciliter l'accès à la lecture et accompagner les enfants et élèves présentant des troubles **DYS** (dyslexie, dyspraxie).")
    
    st.markdown("### 🌟 Ce que propose l'application :")
    st.markdown("* **📄 Aide à la lecture de texte** : Saisissez ou collez n'importe quel texte pour l'adapter instantanément.")
    st.markdown("* **📷 Importation OCR** : Prenez en photo un livre ou une feuille pour en extraire le texte et l'adapter.")
    st.markdown("* **✨ Générateur d'histoires magiques** : Créez des histoires personnalisées selon différents niveaux de difficulté.")
    st.markdown("* **🎤 Aide à la dictée (Propulsée par l'IA)** : Analyse phonétique intelligente, découpage syllabique et génération de dictées contextuelles.")
    st.markdown("* **📐 Grammaire Visuelle & Accords** : Analyse syntaxique par symboles colorés, exercices interactifs d'accords et fiches d'exercices téléchargeables avec code couleur.")


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
        render_full_dys_text(
            st.session_state["histoire_generee"], 
            show_phonemes=opts["show_phonemes"], 
            show_colors=opts["show_colors"], 
            show_arcs=opts["show_arcs"], 
            word_alt=opts["word_alt"], 
            line_alt=opts["line_alt"], 
            soft_bg=opts["soft_bg"], 
            size=opts["size"], 
            key_suffix="histoire_gen"
        )

elif menu_selection == "🎤 Aide à la dictée":
    st.title("🎤 Préparation de la Dictée Personnalisée")
    st.caption("Ophélie Bascou Drimaracci")
    st.write("Saisissez vos mots de la semaine. L'IA va créer la séquence complète d'apprentissage sur 4 jours avec mots à trous et pièges !")
    mots_input = st.text_area(
        "Entrez vos mots (séparés par une virgule, un espace ou un retour à la ligne) :", 
        height=100, 
        placeholder="ex: chat, chien, Mathis, école, vacances..."
    )
    if mots_input:
        opts = build_controls("dictee_ctrl")
        if st.button("🪄 Générer la séquence"):
            with st.spinner("L'IA prépare la séquence de dictée..."):
                prompt = (
                    "À partir de cette liste de mots : " + mots_input + "\n"
                    "Génère un contenu pédagogique structuré pour une séquence de dictée de 4 jours.\n"
                    "Le JSON doit contenir exactement cette structure :\n"
                    "{\n"
                    '    "mots_cles": [...],\n'
                    '    "jour1": [...],\n'
                    '    "jour2": [...],\n'
                    '    "jour3": [...],\n'
                    '    "dictee_finale": "..."\n'
                    "}\n"
                    "Réponds uniquement par le JSON brut, sans markdown."
                )
                res_ia = interroger_ia(prompt, temperature=0.7)
                try:
                    res_json_clean = re.sub(r'```json|```', '', res_ia).strip()
                    st.session_state["data_dictee"] = json.loads(res_json_clean)
                except Exception as e:
                    mots_list = [m.strip() for m in re.split(r'[, \n]+', mots_input) if m.strip()]
                    st.session_state["data_dictee"] = {
                        "mots_cles": mots_list,
                        "jour1": [f"Découverte du mot : {m}" for m in mots_list],
                        "jour2": [f"Complète le mot : {m[:2]}_{m[3:] if len(m)>3 else ''}" for m in mots_list],
                        "jour3": ["Auto-dictée : révise bien les mots appris."],
                        "dictee_finale": f"Voici la dictée avec les mots : {', '.join(mots_list)}."
                    }
        if "data_dictee" in st.session_state:
            data = st.session_state["data_dictee"]
            st.write("---")
            st.subheader("📚 Fiche de travail & Préparation en 4 Étapes")
            tab_j1, tab_j2, tab_j3, tab_j4 = st.tabs([
                "📄 Page 1 : Jour 1 (Découverte & Sons)", 
                "📄 Page 2 : Jour 2 (Mots à trous & Pièges)", 
                "📄 Page 3 : Jour 3 (Auto-dictée)", 
                "📄 Page 4 : Jour 4 (Dictée Finale)"
            ])
            with tab_j1:
                st.markdown("### 🧩 Jour 1 : Découverte des sons & Mots de la semaine")
                mots_texte = " • ".join(data.get("mots_cles", []))
                if mots_texte:
                    render_full_dys_text(mots_texte, key_suffix="j1_mots", **opts)
                st.write("---")
                st.write("**Phrases de découverte :**")
                j1_content = format_to_str(data.get("jour1", ""))
                render_full_dys_text(j1_content, key_suffix="j1_exo", **opts)
            with tab_j2:
                st.markdown("### ✏️ Jour 2 : Mots à trous (Lettres manquantes)")
                j2_content = format_to_str(data.get("jour2", ""))
                render_full_dys_text(j2_content, key_suffix="j2_exo", **opts)
            with tab_j3:
                st.markdown("### 🧠 Jour 3 : Auto-dictée & Mémorisation")
                j3_content = format_to_str(data.get("jour3", ""))
                render_full_dys_text(j3_content, key_suffix="j3_exo", **opts)
            with tab_j4:
                st.markdown("### 🏆 Jour 4 : Dictée Bilan Finale")
                dictee_finale = format_to_str(data.get("dictee_finale", ""))
                render_full_dys_text(dictee_finale, key_suffix="j4_exo", **opts)

elif menu_selection == "📐 Grammaire Visuelle & Accords":
    afficher_page_grammaire(interroger_ia)
