import streamlit as st
import json
import os
import random

def sauvegarder_phrase_dans_historique(phrase):
    if "historique_phrases" not in st.session_state:
        st.session_state["historique_phrases"] = []
    if phrase and phrase not in st.session_state["historique_phrases"]:
        st.session_state["historique_phrases"].append(phrase)
        
# ==========================================
# 1. SYMBOLES ET COULEURS GRAMMATICAUX
# ==========================================
SYMBOLES_GRAMMAIRE = {
    "sujet": {"emoji": "🔴", "label": "Sujet (Rond rouge)", "color": "#e74c3c"},
    "verbe": {"emoji": "🟩", "label": "Verbe (Carré vert)", "color": "#2ecc71"},
    "nom_commun": {"emoji": "⭐", "label": "Nom commun (Étoile jaune)", "color": "#f1c40f"},
    "nom_propre": {"emoji": "✨", "label": "Nom propre (Étoile brillante)", "color": "#f39c12"},
    "determinant": {"emoji": "🔺", "label": "Déterminant (Triangle bleu)", "color": "#3498db"},
    "pronom": {"emoji": "💖", "label": "Pronom (Cœur rose)", "color": "#e84393"},
    "invariable": {"emoji": "⬛", "label": "Mot invariable (Carré noir / Gris)", "color": "#2d3436"}
}

FICHIER_HISTORIQUE = "historique_phrases.json"
MAX_PHRASES = 100

def charger_historique():
    if os.path.exists(FICHIER_HISTORIQUE):
        try:
            with open(FICHIER_HISTORIQUE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def sauvegarder_phrase_dans_historique(nouvelle_phrase):
    historique = charger_historique()
    historique.insert(0, nouvelle_phrase)
    if len(historique) > MAX_PHRASES:
        historique = historique[:MAX_PHRASES]
    with open(FICHIER_HISTORIQUE, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)

def generer_ou_analyser_phrase_ia(fonction_appel_ia, texte_libre=None, niveau=1):
    if texte_libre:
        prompt = f"""
Analyse cette phrase pour un enfant DYS : "{texte_libre}".
Retourne un JSON strict sous cette structure exacte :
{{
  "niveau": {niveau},
  "texte": "{texte_libre}",
  "mots": [
    {{"mot": "Mot", "type": "type_autorise", "is_sujet": false}}
  ],
  "accord": {{
    "phrase_trou": "Mot tronqué avec des traits pour le piège",
    "reponse": "Rien (pas d'accord)",
    "options": ["Rien (pas d'accord)", "s", "e", "ent"]
  }}
}}
Types autorisés : "sujet", "verbe", "nom_commun", "nom_propre", "determinant", "pronom", "invariable".
Réponds UNIQUEMENT avec le JSON.
"""
    else:
        prompt = f"""
Génère une phrase simple en français de niveau {niveau} pour un enfant DYS.
Structure JSON exigée :
{{
  "niveau": {niveau},
  "texte": "Les petits chats dorment.",
  "mots": [
    {{"mot": "Les", "type": "determinant", "is_sujet": false}},
    {{"mot": "petits", "type": "invariable", "is_sujet": false}},
    {{"mot": "chats", "type": "nom_commun", "is_sujet": true}},
    {{"mot": "dorment", "type": "verbe", "is_sujet": false}}
  ],
  "accord": {{
    "phrase_trou": "Les petit___ chat___ dor___.",
    "reponse": "ent",
    "options": ["ent", "e", "s", "Rien (pas d'accord)"]
  }}
}}
Types autorisés : "sujet", "verbe", "nom_commun", "nom_propre", "determinant", "pronom", "invariable".
Réponds UNIQUEMENT avec le JSON.
"""
    try:
        reponse_brute = fonction_appel_ia(prompt).strip()
        if "```" in reponse_brute:
            reponse_brute = reponse_brute.split("```")[1].replace("json", "").strip()
        return json.loads(reponse_brute)
    except Exception:
        return {
            "niveau": niveau,
            "texte": texte_libre if texte_libre else "Les petits chats dorment.",
            "mots": [
                {"mot": "Les", "type": "determinant", "is_sujet": False},
                {"mot": "petits", "type": "invariable", "is_sujet": False},
                {"mot": "chats", "type": "nom_commun", "is_sujet": True},
                {"mot": "dorment", "type": "verbe", "is_sujet": False}
            ],
            "accord": {
                "phrase_trou": "Les petit___ chat___ dor___.",
                "reponse": "ent",
                "options": ["ent", "e", "s", "Rien (pas d'accord)"]
            }
        }

# Dictionnaire complet des symboles et couleurs pour les natures de mots
SYMBOLES_GRAMMAIRE = {
    "determinant": {"emoji": "🔺", "nom": "Déterminant (Triangle bleu)"},
    "det": {"emoji": "🔺", "nom": "Déterminant (Triangle bleu)"},
    
    "pronom": {"emoji": "💖", "nom": "Pronom (Cœur rose)"},
    "pron": {"emoji": "💖", "nom": "Pronom (Cœur rose)"},
    
    "nom": {"emoji": "⭐", "nom": "Nom commun (Étoile jaune)"},
    "nom_commun": {"emoji": "⭐", "nom": "Nom commun (Étoile jaune)"},
    "nom_propre": {"emoji": "✨", "nom": "Nom propre (Étoile brillante)"},
    
    "verbe": {"emoji": "🟩", "nom": "Verbe (Carré vert)"},
    "v": {"emoji": "🟩", "nom": "Verbe (Carré vert)"},
    
    "invariable": {"emoji": "⬛", "nom": "Mot invariable (Carré noir)"},
    "mot_invariable": {"emoji": "⬛", "nom": "Mot invariable (Carré noir)"},
    "adv": {"emoji": "⬛", "nom": "Adverbe / Mot invariable"},
    
    "adjectif": {"emoji": "🔵", "nom": "Adjectif (Cercle bleu)"},
    "adj": {"emoji": "🔵", "nom": "Adjectif"}
}

def afficher_phrase_symboles(phrase_data):
    mots = phrase_data.get("mots", [])
    if not mots:
        st.warning("Aucune phrase à afficher.")
        return

    html_mots = []
    for m in mots:
        type_mot = m.get("type", "").lower()
        
        # Récupération du symbole (cœur, carré, étoile, triangle, etc.)
        info_symb = SYMBOLES_GRAMMAIRE.get(type_mot, {"emoji": "❓"})
        emoji_display = info_symb.get("emoji", "❓")
        
        # Si c'est le sujet identifié, on ajoute le rond rouge distinctif
        if m.get("is_sujet") and type_mot != "sujet":
            emoji_display = f"🔴 {emoji_display}"
        
        mot_texte = m.get('mot', '')
        
        html_mots.append(
            f"<div style='display:inline-block; text-align:center; margin:8px 10px; padding:10px 12px; background:#ffffff; border-radius:8px; border:1px solid #dcdde1; box-shadow: 0 2px 4px rgba(0,0,0,0.05); vertical-align:top;'>"
            f"<div style='font-size:22px; font-weight:bold; color:#2c3e50; margin-bottom:6px;'>{mot_texte}</div>"
            f"<div style='font-size:20px;'>{emoji_display}</div>"
            f"</div>"
        )
        
    st.markdown(
        f"<div style='text-align:center; background:#f8f9fa; padding:15px; border-radius:12px; border:1px solid #e1e8ed;'>{''.join(html_mots)}</div>", 
        unsafe_allow_html=True
    )

def generer_fiche_html_imprimable(phrase_data):
    mots_html = []
    for m in phrase_data["mots"]:
        t = m["type"]
        info_symb = SYMBOLES_GRAMMAIRE.get(t, {"emoji": ""})
        emoji_display = info_symb["emoji"]
        if m.get("is_sujet") and t != "sujet":
            emoji_display = f"🔴 {info_symb['emoji']}"
            
        mots_html.append(f"""
        <div style="display: inline-block; text-align: center; margin: 15px 20px; vertical-align: top;">
            <div style="font-size: 28px; font-weight: bold; font-family: Arial, sans-serif; color: #2c3e50; margin-bottom: 8px;">{m['mot']}</div>
            <div style="font-size: 26px;">{emoji_display}</div>
        </div>
        """)

    accord = phrase_data.get("accord", {})
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="UTF-8"><title>Fiche Grammaire</title></head>
    <body style="font-family: sans-serif; padding: 40px;">
        <h1>📐 Fiche d'Exercice Grammaire & Accords</h1>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; padding: 20px;">{''.join(mots_html)}</div>
        <p style="font-size: 22px; font-weight: bold;">{accord.get('phrase_trou', phrase_data['texte'])}</p>
    </body>
    </html>
    """
# Légende des symboles de grammaire pour les enfants DYS
def afficher_legende_couleurs():
    st.markdown("### 🎨 Légende des symboles grammaticaux")
    
    cols = st.columns(3)
    # Dédoublonnage des symboles pour la légende
    uniques = {}
    for k, v in SYMBOLES_GRAMMAIRE.items():
        emoji = v["emoji"]
        if emoji not in uniques:
            uniques[emoji] = v["nom"]
            
    unique_items = list(uniques.items())
    
    for idx, (emoji, nom) in enumerate(unique_items):
        col_idx = idx % 3
        with cols[col_idx]:
            st.markdown(f"**{emoji}** : {nom}")
    st.markdown("---")
    
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
            st.info("Génération d'une nouvelle phrase...")
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=niveau_sel)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    elif mode_choix == "Écrire ma propre phrase":
    saisie_user = st.text_input("Saisissez votre phrase :", key="input_saisie_libre")
    if st.button("Analyser et ajouter à la banque", key="btn_analyse_libre"):
        if saisie_user.strip():
            with st.spinner("Analyse grammaticale en cours..."):
                nouvelle = generer_ou_analyser_phrase_ia(interroger_ia, texte_force=saisie_user)
            if nouvelle:
                sauvegarder_phrase_dans_historique(nouvelle)
                st.session_state.phrase_grammaire = nouvelle
                st.success("Phrase analysée et sauvegardée !")
            else:
                st.error("Erreur lors de l'analyse par l'IA.")
        else:
            st.warning("Veuillez entrer une phrase valide.")

    elif mode_choix == "Générer une phrase inédite avec l'IA":
       niveau_gen = st.selectbox("Niveau à générer :", ["CP", "CE1", "CE2"], key="select_niveau_gen")
       if st.button("Générer une nouvelle phrase", key="btn_gen_ia"):
          with st.spinner("Génération en cours..."):
            nouvelle = generer_ou_analyser_phrase_ia(interroger_ia, niveau=niveau_gen)
          if nouvelle:
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle
            st.success("Phrase générée et sauvegardée !")
          else:
            st.error("Erreur lors de la génération par l'IA.")

    if "phrase_grammaire" not in st.session_state:
        if historique:
            st.session_state.phrase_grammaire = historique[0]
        else:
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=1)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    phrase = st.session_state.phrase_grammaire
    st.divider()

    # --- SOUS-ONGLETS DE GRAMMAIRE ---
    tab_ex, tab_exo, tab_acc = st.tabs(["📖 Exemple", "✏️ Exercice (Symboles)", "✍️ Accords"])

    with tab_ex:
        st.subheader("Analyse de la phrase")
        afficher_legende_couleurs()
        afficher_phrase_symboles(phrase)

    with tab_exo:
        st.subheader("Identifie le symbole de chaque mot")
        with st.expander("ℹ️ Rappel du code couleur"):
            afficher_legende_couleurs()
            
        mots = phrase["mots"]
        cols = st.columns(len(mots))
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
        st.markdown(f"### {accord.get('phrase_trou', phrase['texte'])}")
        
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
    
