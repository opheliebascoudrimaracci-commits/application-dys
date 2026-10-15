import streamlit as st
import streamlit.components.v1 as components
try:
    import pytesseract
except ImportError:
    pytesseract = None
from PIL import Image, ImageEnhance, ImageFilter
import re
import unicodedata
import random
import hashlib
import json
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
import os
import base64
import sqlite3
from datetime import datetime
from pathlib import Path
from html import escape


def lire_cle_api(nom):
    """Lit une clé depuis Streamlit Secrets ou les variables d'environnement."""
    try:
        valeur = st.secrets.get(nom)
        if valeur:
            return str(valeur).strip()
    except Exception:
        # Streamlit peut lever une exception si aucun fichier de secrets n'existe.
        pass
    return os.environ.get(nom, "").strip()

# Fiche PDF intégrée au programme : aucun fichier PDF séparé n’est nécessaire.
PDF_CODE_COULEUR_BASE64 = """ JVBERi0xLjQKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgKG9wZW5zb3Vy Y2UpCjEgMCBvYmoKPDwKL0YxIDIgMCBSIC9GMiAzIDAgUiAvRjMgNCAwIFIgL0Y0IDUgMCBSIC9G NSA2IDAgUgo+PgplbmRvYmoKMiAwIG9iago8PAovQmFzZUZvbnQgL0hlbHZldGljYSAvRW5jb2Rp bmcgL1dpbkFuc2lFbmNvZGluZyAvTmFtZSAvRjEgL1N1YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250 Cj4+CmVuZG9iagozIDAgb2JqCjw8Ci9CYXNlRm9udCAvSGVsdmV0aWNhLUJvbGQgL0VuY29kaW5n IC9XaW5BbnNpRW5jb2RpbmcgL05hbWUgL0YyIC9TdWJ0eXBlIC9UeXBlMSAvVHlwZSAvRm9udAo+ PgplbmRvYmoKNCAwIG9iago8PAovQmFzZUZvbnQgL1phcGZEaW5nYmF0cyAvTmFtZSAvRjMgL1N1 YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9CYXNlRm9udCAv SGVsdmV0aWNhLU9ibGlxdWUgL0VuY29kaW5nIC9XaW5BbnNpRW5jb2RpbmcgL05hbWUgL0Y0IC9T dWJ0eXBlIC9UeXBlMSAvVHlwZSAvRm9udAo+PgplbmRvYmoKNiAwIG9iago8PAovQmFzZUZvbnQg L1N5bWJvbCAvTmFtZSAvRjUgL1N1YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250Cj4+CmVuZG9iago3 IDAgb2JqCjw8Ci9Db250ZW50cyAxMSAwIFIgL01lZGlhQm94IFsgMCAwIDU5NS4yNzU2IDg0MS44 ODk4IF0gL1BhcmVudCAxMCAwIFIgL1Jlc291cmNlcyA8PAovRm9udCAxIDAgUiAvUHJvY1NldCBb IC9QREYgL1RleHQgL0ltYWdlQiAvSW1hZ2VDIC9JbWFnZUkgXQo+PiAvUm90YXRlIDAgL1RyYW5z IDw8Cgo+PiAKICAvVHlwZSAvUGFnZQo+PgplbmRvYmoKOCAwIG9iago8PAovUGFnZU1vZGUgL1Vz ZU5vbmUgL1BhZ2VzIDEwIDAgUiAvVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKOSAwIG9iago8PAov QXV0aG9yIChcKGFub255bW91c1wpKSAvQ3JlYXRpb25EYXRlIChEOjIwMjYxMDE1MTIxODA2KzAw JzAwJykgL0NyZWF0b3IgKFwodW5zcGVjaWZpZWRcKSkgL0tleXdvcmRzICgpIC9Nb2REYXRlIChE OjIwMjYxMDE1MTIxODA2KzAwJzAwJykgL1Byb2R1Y2VyIChSZXBvcnRMYWIgUERGIExpYnJhcnkg LSBcKG9wZW5zb3VyY2VcKSkgCiAgL1N1YmplY3QgKFwodW5zcGVjaWZpZWRcKSkgL1RpdGxlIChc KGFub255bW91c1wpKSAvVHJhcHBlZCAvRmFsc2UKPj4KZW5kb2JqCjEwIDAgb2JqCjw8Ci9Db3Vu dCAxIC9LaWRzIFsgNyAwIFIgXSAvVHlwZSAvUGFnZXMKPj4KZW5kb2JqCjExIDAgb2JqCjw8Ci9G aWx0ZXIgWyAvQVNDSUk4NURlY29kZSAvRmxhdGVEZWNvZGUgXSAvTGVuZ3RoIDE5ODQKPj4Kc3Ry ZWFtCkdiITtkPWA8JVMmOlZzL1FxLWxWL0tWSywvL0RzYyJwbz4jRVYmNi1gRl4obltjSF5FR1E3 V2U6a3JVZF4mbWEpKV5EZF5jTEklcDMmOzZSJFU8RW9PKEpCISMxMz1vSkk8O1chRVZ0MmkhT2Rf UEAjXU1QZEQxY1QnKElZXHIkZWVcWXQ7JE4lPDFaI0ZMVFhcZTpBRVtka1QwUz1pR1tIVTMhN29I OFsyaj9YJ1djXXVKNk9yZlZvYG0/YTdUM1lmcj8xYEw1RSxrb2FHQk1HXyNEM2cwXVNGc0k4XTo5 KDVBZic+LThzJFVEaCpHJ1s+TidFLisyUmJuMSNqRF9wUGZGZmhnQ00oO2lyU1psImldSWNYTSEt X043ZEU2dCVJRlVEWFYlbjw8Uik1ZGtYOUQ1ZG8oMmhsOTkmJmtVPllPNl8yQiNfaEp1aSVbZkly X2tkLD5EOW9GZkZWY0MwNWkxMFs+LDViJy8jXjgqdSRJZCxiMSsuUEZoTyVAVSo2ITU2cXBZZihC ODJOSEI3alojI085KiguOFk7QVgkWF9GVjtMbWReOS1WTVdoIk9eZ1ohOic6PydLOSRZKUQ/UUct LUMkZSJZbGQ+bjUpUDdDJUpJcCQuVk81LjBUbl9MckNdKzlKNyc5JitGP2AhJmAtXEVzcXA8MjZH Q0YmQXIzOCFXXFNNbEc+NGIjMVs4YytaY24iciJ1MFRsWWJyRF1wcSlBJlNWRCptb2olQUBWWWRw KSRUdTdMJEFHIVU/ZlxEaDlPXGFjKDsuYFMhXjZfWTBEZWpQL0w8RCdhM2koS1pGKUtzIlphYSVn MDA8Z1U5TGRQT2NQNnQpdGFOPUxCNlA/QV8rOzAtPVlTXS5zLlYxK3ExRk0iVV5eM3BFO0twQnFo JmtESi4jSFVocytbY05OUiI+Xks0OWhuKDknOWU2VkdjbkEkKTVbO0FiMEQ+Ll1kXzVGUmxyWDtp UE44XG9GOW9JZ2YjKVEtUyhYNz89YkRCYTpfO3E/cT1uajdYTClwUGJVLTMuaW8yJT9gRGlTRjBS YzZLTDw5ZHRUITlwZTFPNzNGUWU/M0sjSCg0QkxKY3BXbFkpPmxVdFVhSy8sXmU9KzdmKTZrK1ll bCZeJU9CWThfPkc3Iykocjk2OV9PI0I+Xz9WRUtgO2hmcklgckZfSVZgIV5RakZRLGZWblg4ZSRa LDo8dUhQJD0zaDhtX0E6LD1kVyIkQGBkX2VTKkFFJGRYYFArUjNpKCNoIyY+OFcnSyRIN2w0SGoq PV1KaztQR1tqdVVkMXAuTk5tczZQazFeaUBuNCcwWTBTWG1VZzM+T3BIOVVkQXFbInJLaUpNZ1Yu ayJLYT1wJWRDJCQ8KThMRVJKL2EmX2ovP1MlW15fRldcVFwkcm1cMmgvPTVeaF1jWXEhXllrNiVm U0AoYFNGPGRrUF1FLSRCPmBOKEZoPSZoPWEpTkwuXlMjS1AnbzNgMkZnZy5ec19IKE1zaSpyLUFd JjgwMDInJ00kOCU/UlZjN0RMVnEpIiZBOlNxIyJVRypWI1dzSSwjN01iQVQpVzxOMy03R3NabVgx SE5UcTJiTzEkSlM0QjYzKGBWW0JdL1NLaylcRi0mXHMrPE5lRWxNcy9RbGZEITtSLT9KSltbWEIr bC45Pi9wNDxpN2AtLk8vY0NTamtDNz9hOl5MY2BhXCcqWFtfOFowSyRWcTVkYXUkWkldZGFSKlY7 UEVNLE4wQCEnWFtXYDlcNExjais9PSsvb0c8LSpuOkNibFJeOEE4ZzEzWEpTOFZARk8+ZmVZLj1F RVNTP1dkOj09UG0tXlFJOT5BbSRLIURGLGRZaj9kQGs6dSgrLVMidFtJNWwtcERSXmhKaVxLN0Uz WFZKakBRUlNESW1nPG5vbCU8PC1JMlc7Vk9tTyNKKTlqU1lTYmltW05QP1RTWyVvUjA3Lz9FYUFo bGMvJD1XREcjajtJJ1BoY3JuRml1JzJuPTQ1O0RldVNnLWAoRFY+JDl0bk9pSXFiNl5sJiNoJlc+ Qi5gcj0vbV9mNjorYUk7ZkI2N0ZzK1g6N2AmViJzbzRzUlRpbjlfJyZLOlROXDBfaTtqPDxfRDN1 ciN0Z3U0QFlyP21XYF1gRT5qUFRWTloxPkMsMzoxYixIUzU6aClJdS81LVxRJiVJU1RQWlcpNj4p XWhZaFVEUykxTUM7Yy0iUldLaWRvKCdGRjohY0IkXFdsJWlJJEF1O3BmZV47V19EbkYuMWtZVGZR KCltL1NaZ01CPmRbPT5jSlZUMWJhOz0vUjhjVFptOk88PCMvXEg/U29tQFFnaD80aUVMLCY4X0o7 aCYkNS9BTTFmQ04xNDouV0hBJzJhX08vNV5SMFpcLllMdHJDLjFyPFkoOGY2IzIyJUliMS4pYihk TnQlNHBaUTxlLENVIlpPKUo7XUhwbjNgWEAwMyZaYGVbPyVHcUQ6XzwsYG9oMkYmNU5xLV48YypQ Xi01W0djbkBHN1NoTydsPU9eVk10dS0zJ1M3Z00xLDkqNldsS0g4SCFSJVhhJE5OUFNXYFBrXTJD OU1iWFVKTm9mUkJda3RjZjgsW11LZFpDRz42THU4cEU+aDY/PE1YVSkmKHIlZG5Hfj5lbmRzdHJl YW0KZW5kb2JqCnhyZWYKMCAxMgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwNjEgMDAwMDAg biAKMDAwMDAwMDEzMiAwMDAwMCBuIAowMDAwMDAwMjM5IDAwMDAwIG4gCjAwMDAwMDAzNTEgMDAw MDAgbiAKMDAwMDAwMDQzNCAwMDAwMCBuIAowMDAwMDAwNTQ5IDAwMDAwIG4gCjAwMDAwMDA2MjYg MDAwMDAgbiAKMDAwMDAwMDgzMSAwMDAwMCBuIAowMDAwMDAwOTAwIDAwMDAwIG4gCjAwMDAwMDEx ODAgMDAwMDAgbiAKMDAwMDAwMTI0MCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9JRCAKWzxjMjRmNDUy ZWY1YjM4ZjUwMGM5NTVkNmJjMzQzMzEyMj48YzI0ZjQ1MmVmNWIzOGY1MDBjOTU1ZDZiYzM0MzMx MjI+XQolIFJlcG9ydExhYiBnZW5lcmF0ZWQgUERGIGRvY3VtZW50IC0tIGRpZ2VzdCAob3BlbnNv dXJjZSkKCi9JbmZvIDkgMCBSCi9Sb290IDggMCBSCi9TaXplIDEyCj4+CnN0YXJ0eHJlZgozMzE2 CiUlRU9GCg== """

def telecharger_pdf_code_couleur():
    """Renvoie les octets du PDF embarqué dans ce fichier Python."""
    return base64.b64decode(PDF_CODE_COULEUR_BASE64)

# ==========================================
# UTILITAIRE IA CENTRALISÉ (Groq / Gemini)
# ==========================================
def interroger_ia(prompt_texte, temperature=0.8):
    """IA appelée uniquement après une action explicite de l'adulte."""
    erreurs = []
    groq_key = lire_cle_api("GROQ_API_KEY")
    if groq_key and OpenAI is not None:
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
                    erreurs.append(f"Groq ({g_model}) : {e_inner}")
        except Exception as e:
            erreurs.append(f"Groq Init : {e}")
    elif not groq_key:
        erreurs.append("Groq : Clé 'GROQ_API_KEY' absente")
    else:
        erreurs.append("Client Groq indisponible : installez le paquet openai si vous souhaitez activer l'IA.")

    gemini_key = lire_cle_api("GEMINI_API_KEY")
    if gemini_key and genai is not None:
        try:
            genai.configure(api_key=gemini_key.strip())
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt_texte, generation_config={"temperature": temperature})
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            erreurs.append(f"Gemini : {e}")
    elif not gemini_key:
        erreurs.append("Gemini : Clé 'GEMINI_API_KEY' absente")
    else:
        erreurs.append("Client Gemini indisponible : installez google-generativeai si vous souhaitez activer l'IA.")
    return f"Erreur IA -> " + " | ".join(erreurs)

# ==========================================
# SAUVEGARDE LOCALE ET SUIVI PEDAGOGIQUE
# ==========================================
DB_PATH = Path(os.environ.get("APP_PEDAGOGIQUE_DB", "application_pedagogique_data.sqlite3"))


def connexion_db():
    """Ouvre la base SQLite locale; les résultats persistent entre les sessions."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialiser_db():
    with connexion_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS resultats ( id INTEGER PRIMARY KEY AUTOINCREMENT, eleve TEXT NOT NULL, niveau TEXT NOT NULL, notion TEXT NOT NULL, question TEXT NOT NULL, reponse TEXT NOT NULL, bonne_reponse TEXT NOT NULL, correct INTEGER NOT NULL, date_utc TEXT NOT NULL )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS preferences ( cle TEXT PRIMARY KEY, valeur TEXT NOT NULL )""")


def lire_preference(cle, defaut=""):
    with connexion_db() as conn:
        row = conn.execute("SELECT valeur FROM preferences WHERE cle=?", (cle,)).fetchone()
    return row["valeur"] if row else defaut


def enregistrer_preference(cle, valeur):
    with connexion_db() as conn:
        conn.execute("INSERT INTO preferences(cle,valeur) VALUES(?,?) ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur", (cle, str(valeur)))


def enregistrer_resultat(eleve, niveau, exercice, reponse, correct):
    with connexion_db() as conn:
        conn.execute("INSERT INTO resultats(eleve,niveau,notion,question,reponse,bonne_reponse,correct,date_utc) VALUES(?,?,?,?,?,?,?,?)",
                     (eleve, niveau, exercice["notion"], exercice["question"], str(reponse), exercice["reponse"], int(correct), datetime.now().astimezone().isoformat(timespec="seconds")))


def lire_resultats(eleve):
    with connexion_db() as conn:
        rows = conn.execute("SELECT * FROM resultats WHERE eleve=? ORDER BY id DESC", (eleve,)).fetchall()
    return [dict(r) for r in rows]


BANQUE_EXERCICES = [
    {"notion":"Déterminant et nom", "niveaux":["CP","CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Choisis la phrase correctement accordée.", "options":["Les petit chat dort.","Le petit chat dort.","La petit chat dort."], "reponse":"Le petit chat dort.", "explication":"« Le » est un déterminant masculin singulier, comme « chat ». « Petit » s’accorde avec le nom : masculin singulier."},
    {"notion":"Pluriel", "niveaux":["CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Complète : « Les cheval___ galopent. »", "options":["cheval","chevaux","chevals"], "reponse":"chevaux", "explication":"Le pluriel de « cheval » est « chevaux » : les noms en -al font souvent leur pluriel en -aux."},
    {"notion":"Accord sujet-verbe", "niveaux":["CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Choisis la bonne forme : « Les enfants ___ dans la cour. »", "options":["joue","jouent","joues"], "reponse":"jouent", "explication":"Le sujet « les enfants » est à la 3e personne du pluriel : le verbe prend ici -ent."},
    {"notion":"Accord de l’adjectif", "niveaux":["CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Complète : « Une robe ___ »", "options":["bleu","bleue","bleues"], "reponse":"bleue", "explication":"« Robe » est féminin singulier. L’adjectif « bleu » prend un -e : « bleue »."},
    {"notion":"Homophones", "niveaux":["CM1","CM2","Collège","Adulte"], "question":"Complète : « ___ vélo est rouge. »", "options":["Son","Sont","Sans"], "reponse":"Son", "explication":"« Son » est un déterminant possessif. On peut essayer de le remplacer par « mon » : « mon vélo »."},
    {"notion":"Homophones", "niveaux":["CM1","CM2","Collège","Adulte"], "question":"Complète : « Ils ___ terminé leurs devoirs. »", "options":["on","ont","où"], "reponse":"ont", "explication":"« Ont » est le verbe avoir conjugué au présent. On peut le remplacer par « avaient » : « Ils avaient terminé leurs devoirs »."},
    {"notion":"Conjugaison", "niveaux":["CE2","CM1","CM2","Collège","Adulte"], "question":"Au présent : « Nous ___ une chanson. » (chanter)", "options":["chantons","chantez","chantent"], "reponse":"chantons", "explication":"Avec « nous », le verbe chanter au présent se conjugue « nous chantons »."},
    {"notion":"Nature des mots", "niveaux":["CE2","CM1","CM2","Collège","Adulte"], "question":"Dans « Le chien aboie », quel mot est le verbe ?", "options":["Le","chien","aboie"], "reponse":"aboie", "explication":"« Aboie » exprime l’action : c’est le verbe. « Le » est un déterminant et « chien » est un nom."},
    {"notion":"Ponctuation", "niveaux":["CP","CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Quel signe termine généralement une question ?", "options":["?",".",","], "reponse":"?", "explication":"Une question directe se termine par un point d’interrogation : ?."},
    {"notion":"Accord sujet-verbe", "niveaux":["CM1","CM2","Collège","Adulte"], "question":"Choisis la phrase correcte.", "options":["Toi et Lina arrivez demain.","Toi et Lina arrive demain.","Toi et Lina arrives demain."], "reponse":"Toi et Lina arrivez demain.", "explication":"« Toi et Lina » correspond à « vous » : le verbe se conjugue à la 2e personne du pluriel, « arrivez »."},
    {"notion":"Infinitif ou participe passé", "niveaux":["CM2","Collège","Adulte"], "question":"Complète : « Elle a ___ son devoir. »", "options":["terminer","terminé","terminée"], "reponse":"terminé", "explication":"Avec l’auxiliaire « avoir », on utilise ici le participe passé « terminé ». Le complément direct est placé après le verbe."},
    {"notion":"Lecture", "niveaux":["CP","CE1","CE2","CM1","CM2","Collège","Adulte"], "question":"Dans « Lina prend son parapluie car il pleut », pourquoi Lina prend-elle son parapluie ?", "options":["Parce qu’il pleut.","Parce qu’il fait chaud.","Parce qu’elle veut dormir."], "reponse":"Parce qu’il pleut.", "explication":"La réponse est donnée dans la phrase par le mot « car », qui introduit la raison."},
]


def filtrer_exercices(niveau, notion="Toutes"):
    exercices = [e for e in BANQUE_EXERCICES if niveau in e["niveaux"] and (notion == "Toutes" or e["notion"] == notion)]
    return exercices or [e for e in BANQUE_EXERCICES if niveau in e["niveaux"]]


def afficher_entrainement(eleve, niveau):
    st.title("🎯 Entraînement interactif")
    st.caption("Réponds, vérifie ta réponse, puis lis l’explication pour comprendre la règle.")
    notions = ["Toutes"] + sorted({e["notion"] for e in BANQUE_EXERCICES if niveau in e["niveaux"]})
    notion = st.selectbox("Choisir une notion", notions, key="entrainement_notion")
    pool = filtrer_exercices(niveau, notion)
    if "exo_courant_id" not in st.session_state or st.session_state.get("exo_courant_niveau") != niveau or st.session_state.get("exo_courant_notion") != notion:
        st.session_state.exo_courant_id = random.randrange(len(pool))
        st.session_state.exo_session_numero = st.session_state.get("exo_session_numero", 0) + 1
        st.session_state.exo_courant_niveau = niveau
        st.session_state.exo_courant_notion = notion
        st.session_state.pop("exo_resultat_affiche", None)
    exo = pool[st.session_state.exo_courant_id % len(pool)]
    st.caption(f"Niveau sélectionné : {niveau} · Entraînement sans chronomètre")
    st.subheader(exo["notion"])
    st.markdown(f"### {exo['question']}")
    reponse = st.radio("Ta réponse", exo["options"], key=f"reponse_exo_{st.session_state.get('exo_session_numero', 1)}_{st.session_state.exo_courant_id}_{niveau}_{notion}", label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Vérifier ma réponse", type="primary", use_container_width=True):
            correct = reponse == exo["reponse"]
            st.session_state.exo_resultat_affiche = {"correct": correct, "reponse": reponse, "question": exo["question"]}
            enregistrer_resultat(eleve, niveau, exo, reponse, correct)
    with col2:
        if st.button("➡️ Autre exercice", use_container_width=True):
            st.session_state.exo_courant_id = random.randrange(len(pool))
            st.session_state.exo_session_numero = st.session_state.get("exo_session_numero", 0) + 1
            st.session_state.pop("exo_resultat_affiche", None)
            st.rerun()
    resultat = st.session_state.get("exo_resultat_affiche")
    if resultat and resultat.get("question") == exo["question"]:
        if resultat["correct"]:
            st.success("Bravo, c’est la bonne réponse ! 🎉")
        else:
            st.error(f"Pas tout à fait. La bonne réponse est : **{exo['reponse']}**")
        st.info("**Pourquoi ?** " + exo["explication"])


def afficher_progres(eleve):
    st.title("📊 Mes progrès")
    resultats = lire_resultats(eleve)
    if not resultats:
        st.info("Aucun résultat enregistré pour le moment. Fais un exercice pour commencer ton suivi.")
        return
    total = len(resultats)
    justes = sum(r["correct"] for r in resultats)
    c1, c2, c3 = st.columns(3)
    c1.metric("Exercices réalisés", total)
    c2.metric("Réponses correctes", justes)
    c3.metric("Réussite", f"{round(100*justes/total)} %")
    st.subheader("Résultats par notion")
    stats = {}
    for r in resultats:
        d = stats.setdefault(r["notion"], {"Réussites": 0, "Essais": 0})
        d["Essais"] += 1
        d["Réussites"] += int(r["correct"])
    lignes = [{"Notion": k, "Réussites": v["Réussites"], "Essais": v["Essais"], "Pourcentage": round(100*v["Réussites"]/v["Essais"])} for k,v in stats.items()]
    st.dataframe(lignes, use_container_width=True, hide_index=True)
    st.subheader("Derniers exercices")
    st.dataframe([{"Date": r["date_utc"], "Niveau": r["niveau"], "Notion": r["notion"], "Résultat": "Réussi" if r["correct"] else "À revoir", "Question": r["question"]} for r in resultats[:20]], use_container_width=True, hide_index=True)
    if stats:
        a_revoir = [k for k,v in stats.items() if v["Réussites"]/v["Essais"] < 0.7]
        if a_revoir:
            st.warning("Notions à retravailler : " + ", ".join(a_revoir))
        else:
            st.success("Très bon travail ! Tes résultats sont solides dans les notions essayées.")




# ==========================================================
# EXTENSIONS AJOUTÉES — profils, bibliothèque, impression, sons
# Les modules d'origine ci-dessus restent inchangés.
# ==========================================================
def initialiser_extensions():
    with connexion_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS profils ( nom TEXT PRIMARY KEY, niveau TEXT NOT NULL DEFAULT 'CE1', preferences_json TEXT NOT NULL DEFAULT '{}', cree_le TEXT NOT NULL )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS histoires ( id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT NOT NULL, contenu TEXT NOT NULL, source TEXT NOT NULL, niveau TEXT NOT NULL, sons_cibles TEXT NOT NULL DEFAULT '', interets TEXT NOT NULL DEFAULT '', statut TEXT NOT NULL DEFAULT 'approuvee', cree_par TEXT NOT NULL, cree_le TEXT NOT NULL )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS historique_histoires ( id INTEGER PRIMARY KEY AUTOINCREMENT, eleve TEXT NOT NULL, histoire_id INTEGER NOT NULL, proposee_le TEXT NOT NULL, FOREIGN KEY(histoire_id) REFERENCES histoires(id) )""")
        conn.execute("INSERT OR IGNORE INTO profils(nom,niveau,cree_le) VALUES(?,?,?)",
                     (lire_preference("eleve_actif
