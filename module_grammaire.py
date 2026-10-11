import streamlit as st
import json
import os
import random

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

# ==========================================
# 2. GESTION DE LA MÉMOIRE DES 100 PHRASES (FIFO)
# ==========================================
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
    historique.insert(0, nouvelle_phrase)  # Ajout en tête
    if len(historique) > MAX_PHRASES:
        historique = historique[:MAX_PHRASES]  # La 101e est supprimée
    with open(FICHIER_HISTORIQUE, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)

# ==========================================
# 3. INTERACTION IA & SECOURS
# ==========================================
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
    "phrase_trou": "Mot tronqué avec des traits pour le piège (ex: petit___, dor___)",
    "reponse": "Rien (pas d'accord)" ou "s" ou "e" ou "ent",
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

# ==========================================
# 4. AFFICHAGE DE LA LÉGENDE ET DES MOTS
# ==========================================
def afficher_legende_couleurs():
    """ Affiche le rappel visuel des couleurs et symboles grammaticales """
    st.markdown("""
    <div style="background-color: #f1f3f5; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3498db;">
        <h4 style="margin-top: 0; color: #2c3e50;">🎨 Code couleur et symboles :</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 15px;">
            <div>🔴 <b>Sujet</b> (Rond rouge)</div>
            <div>🟩 <b>Verbe</b> (Carré vert)</div>
            <div>⭐ <b>Nom commun</b> (Étoile jaune)</div>
            <div>✨ <b>Nom propre</b> (Étoile brillante)</div>
            <div>🔺 <b>Déterminant</b> (Triangle bleu)</div>
            <div>💖 <b>Pronom</b> (Cœur rose)</div>
            <div>⬛ <b>Mot invariable</b> (Carré noir / Gris)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def afficher_phrase_symboles(phrase_data):
    html_mots = []
    for m in phrase_data["mots"]:
        type_mot = m["type"]
        info_symb = SYMBOLES_GRAMMAIRE.get(type_mot, {"emoji": ""})
        
        emoji_display = info_symb["emoji"]
        if m.get("is_sujet") and type_mot != "sujet":
            emoji_display = f"🔴 {info_symb['emoji']}"
            
        html_mots.append(f"""
        <div style="display: inline-block; text-align: center; margin: 8px 14px; vertical-align: top;">
            <div style="font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 6px;">{m['mot']}</div>
            <div style="font-size: 22px;">{emoji_display}</div>
        </div>
        """)
        
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: center; padding: 20px; background-color: #f8f9fa; border-radius: 12px; border: 1px solid #dee2e6; margin: 15px 0;">
        {''.join(html_mots)}
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. FONCTION PRINCIPALE APPELÉE PAR STREAMLIT
# ==========================================
def afficher_page_grammaire(fonction_appel_ia):
    st.header("📐 Module Grammaire Visuelle & Accords")
    
    mode_choix = st.radio(
        "Source de la phrase :",
        ["Piocher dans la banque de 100 phrases", "Écrire ma propre phrase", "Générer une phrase inédite avec l'IA"],
        horizontal=True
    )

    historique = charger_historique()

    if mode_choix == "Piocher dans la banque de 100 phrases":
        niveau_sel = st.selectbox("Sélectionner le niveau :", [1, 2, 3], format_func=lambda x: f"Niveau {x}")
        phrases_dispos = [p for p in historique if p.get("niveau") == niveau_sel]
        
        if phrases_dispos:
            st.session_state.phrase_grammaire = random.choice(phrases_dispos)
        else:
            st.info("Aucune phrase de ce niveau en mémoire. Génération d'une nouvelle phrase...")
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=niveau_sel)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    elif mode_choix == "Écrire ma propre phrase":
        saisie_user = st.text_input("Saisissez votre phrase ici :")
        if st.button("Analyser et ajouter à la banque") and saisie_user:
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, texte_libre=saisie_user)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle
            st.success("Phrase analysée et sauvegardée !")

    elif mode_choix == "Générer une phrase inédite avec l'IA":
        niveau_gen = st.selectbox("Niveau à générer :", [1, 2, 3])
        if st.button("Générer une nouvelle phrase"):
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=niveau_gen)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    if "phrase_grammaire" not in st.session_state:
        if historique:
            st.session_state.phrase_grammaire = historique[0]
        else:
            nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, niveau=1)
            sauvegarder_phrase_dans_historique(nouvelle)
            st.session_state.phrase_grammaire = nouvelle

    phrase = st.session_state.phrase_grammaire

    # --- BOUTON DE TÉLÉCHARGEMENT DE LA FICHE ---
    st.divider()
    html_fiche = generer_fiche_html_imprimable(phrase)
    
    st.download_button(
        label="📥 Télécharger la fiche d'exercice (avec code couleur)",
        data=html_fiche,
        file_name=f"fiche_grammaire_niveau_{phrase.get('niveau', 1)}.html",
        mime="text/html",
        type="primary"
    )

    st.divider()

    # --- SOUS-ONGLETS ---
    tab_ex, tab_exo, tab_acc = st.tabs(["📖 Exemple (Démonstration)", "✏️ Exercice (Symboles)", "✍️ Accords Grammaticaux"])

    # 1. EXEMPLE (Avec la légende intégrée)
    with tab_ex:
        st.subheader("Analyse de la phrase")
        afficher_legende_couleurs()
        afficher_phrase_symboles(phrase)

    # 2. EXERCICE SYMBOLES
    with tab_exo:
        st.subheader("Identifie le symbole de chaque mot")
        # On peut aussi afficher la légende ici en version repliable ou directe si besoin
        with st.expander("ℹ️ Rappel du code couleur"):
            afficher_legende_couleurs()
            
        mots = phrase["mots"]
        cols = st.columns(len(mots))
        choix_eleve = {}
        
        for idx, m in enumerate(mots):
            with cols[idx]:
                st.markdown(f"<h4 style='text-align: center;'>{m['mot']}</h4>", unsafe_allow_html=True)
                choix_eleve[idx] = st.selectbox(
                    f"Symbole {idx}",
                    ["-- Choisir --"] + [s["label"] for s in SYMBOLES_GRAMMAIRE.values()],
                    key=f"symb_sel_{idx}",
                    label_visibility="collapsed"
                )

        if st.button("Valider mes symboles", type="primary"):
            exact = True
            for idx, m in enumerate(mots):
                label_attendu = SYMBOLES_GRAMMARE = SYMBOLES_GRAMMAIRE.get(m["type"], {}).get("label", "")
                if choix_eleve[idx] != label_attendu:
                    exact = False
            if exact:
                st.balloons()
                st.success("Bravo ! Tous les symboles sont corrects ! 🎉")
            else:
                st.warning("Il y a des erreurs. Vérifie dans l'onglet Exemple !")

    # 3. ACCORDS
    with tab_acc:
        st.subheader("Exercice d'accord : Faut-il accorder ?")
        accord = phrase.get("accord", {})
        
        st.markdown(f"### {accord.get('phrase_trou', phrase['texte'])}")
        
        choix_accord = st.radio(
            "Sélectionne la réponse correcte :",
            options=accord.get("options", ["Rien (pas d'accord)", "s", "e", "ent"]),
            horizontal=True
        )
        
        if st.button("Vérifier l'accord"):
            if choix_accord == accord.get("reponse"):
                st.balloons()
                st.success("Excellente réponse ! 🌟")
            else:
                st.error(f"Attention ! La bonne réponse était : '{accord.get('reponse')}'")

# ==========================================
# FONCTION D'EXPORTATION AVEC CODE COULEUR
# ==========================================
def generer_fiche_html_imprimable(phrase_data):
    """ Génère un fichier HTML autonome imprimable avec le code couleur complet """
    mots_html = []
    for m in phrase_data["mots"]:
        t = m["type"]
        info_symb = SYMBOLES_GRAMMAIRE.get(t, {"emoji": ""})
        
        emoji_display = info_symb["emoji"]
        if m.get("is_sujet") and t != "sujet":
            emoji_display = f"🔴 {info_symb['emoji']}"
            
        mots_html.append(f"""
        <div style="display: inline-block; text-align: center; margin: 15px 20px; vertical-align: top;">
            <div style="font-size: 28px; font-weight: bold; font-family: 'OpenDyslexic', Arial, sans-serif; color: #2c3e50; margin-bottom: 8px;">{m['mot']}</div>
            <div style="font-size: 26px;">{emoji_display}</div>
        </div>
        """)

    accord = phrase_data.get("accord", {})

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Fiche d'exercice Grammaire DYS</title>
        <style>
            body {{
                font-family: 'OpenDyslexic', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 40px;
                background-color: #ffffff;
                color: #2c3e50;
            }}
            .titre {{
                text-align: center;
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }}
            .legende {{
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 30px;
            }}
            .legende-items {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                font-size: 16px;
            }}
            .zone-phrase {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                padding: 30px;
                background-color: #fafafa;
                border: 2px dashed #cbd5e1;
                border-radius: 12px;
                margin-bottom: 40px;
            }}
            .section-accord {{
                background-color: #f1f5f9;
                padding: 20px;
                border-radius: 10px;
            }}
            @media print {{
                body {{ padding: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: right; margin-bottom: 20px;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; background-color: #2ecc71; color: white; border: none; border-radius: 5px; cursor: pointer;">
                🖨️ Imprimer / Enregistrer en PDF
            </button>
        </div>

        <h1 class="titre">📐 Fiche d'Exercice Grammaire & Accords</h1>

        <div class="legende">
            <h3>🎨 Légende du code couleur et symboles :</h3>
            <div class="legende-items">
                <div>🔴 <b>Sujet</b> (Rond rouge)</div>
                <div>🟩 <b>Verbe</b> (Carré vert)</div>
                <div>⭐ <b>Nom commun</b> (Étoile jaune)</div>
                <div>✨ <b>Nom propre</b> (Étoile brillante)</div>
                <div>🔺 <b>Déterminant</b> (Triangle bleu)</div>
                <div>💖 <b>Pronom</b> (Cœur rose)</div>
                <div>⬛ <b>Mot invariable</b> (Carré noir)</div>
            </div>
        </div>

        <h2>1. Analyse visuelle de la phrase :</h2>
        <div class="zone-phrase">
            {''.join(mots_html)}
        </div>

        <h2>2. Exercice d'accord :</h2>
        <div class="section-accord">
            <p style="font-size: 22px; font-weight: bold;">{accord.get('phrase_trou', phrase_data['texte'])}</p>
            <p><b>Choix possibles :</b> {', '.join(accord.get('options', []))}</p>
        </div>
    </body>
    </html>
    """
    return html_content
    
