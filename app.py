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
                    
                    # RÈGLE DU VERBE EN -ENT : Si c'est un verbe avec un sujet au pluriel, -ent N'EST PAS une nasale [an]
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
    
def count_syllables_approx(word):
    import re
    word = word.lower()
    if word.endswith('e') and len(word) > 1:
        word = word[:-1]
    vowels = re.findall(r'[aeiouyàâäéèêëîïôöùûüÿœæ]+', word)
    return max(1, len(vowels))

def render_full_dys_text(text, show_phonemes=True, show_colors=True, word_alt=False, line_alt=False, size=18, soft_bg=True, **kwargs):
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for idx, word in enumerate(words):
            # Récupération du mot précédent pour la grammaire (sujets pluriels)
            prev_word = words[idx - 1] if idx > 0 else ""
            
            # Rendu du mot avec son contexte
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
    
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2; color: #111111;" if soft_bg else ""
    
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
    

def render_full_dys_text(text, show_phonemes=True, show_colors=True, word_alt=False, line_alt=False, size=18, soft_bg=True, **kwargs):
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for idx, word in enumerate(words):
            # Récupération du mot précédent pour la grammaire (sujets pluriels)
            prev_word = words[idx - 1] if idx > 0 else ""
            
            # Rendu du mot avec son contexte
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
    
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5


def render_full_dys_text(text, show_phonemes=True, show_colors=True, word_alt=False, line_alt=False, size=18, soft_bg=True, **kwargs):
    lines = text.split('\n')
    rendered_lines_adapted = []
    rendered_lines_training = []
    
    for line_idx, line in enumerate(lines):
        words = line.split()
        rendered_words_adapted = []
        rendered_words_training = []
        
        for idx, word in enumerate(words):
            # On récupère le mot juste avant (s'il existe)
            prev_word = words[idx - 1] if idx > 0 else ""
            
            # On transmet ce mot précédent à votre fonction
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
    
    style_bg = "background-color: #f4f6f9; padding: 15px; border-radius: 8px; border-left: 5px solid #4a90e2; color: #111111;" if soft_bg else ""
    
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
