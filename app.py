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
    "pronom": {"label": "Pronom", "emoji": "💖", "couleur": "#9b
