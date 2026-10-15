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
PDF_CODE_COULEUR_BASE64 = """
JVBERi0xLjQKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgKG9wZW5zb3Vy
Y2UpCjEgMCBvYmoKPDwKL0YxIDIgMCBSIC9GMiAzIDAgUiAvRjMgNCAwIFIgL0Y0IDUgMCBSIC9G
NSA2IDAgUgo+PgplbmRvYmoKMiAwIG9iago8PAovQmFzZUZvbnQgL0hlbHZldGljYSAvRW5jb2Rp
bmcgL1dpbkFuc2lFbmNvZGluZyAvTmFtZSAvRjEgL1N1YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250
Cj4+CmVuZG9iagozIDAgb2JqCjw8Ci9CYXNlRm9udCAvSGVsdmV0aWNhLUJvbGQgL0VuY29kaW5n
IC9XaW5BbnNpRW5jb2RpbmcgL05hbWUgL0YyIC9TdWJ0eXBlIC9UeXBlMSAvVHlwZSAvRm9udAo+
PgplbmRvYmoKNCAwIG9iago8PAovQmFzZUZvbnQgL1phcGZEaW5nYmF0cyAvTmFtZSAvRjMgL1N1
YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9CYXNlRm9udCAv
SGVsdmV0aWNhLU9ibGlxdWUgL0VuY29kaW5nIC9XaW5BbnNpRW5jb2RpbmcgL05hbWUgL0Y0IC9T
dWJ0eXBlIC9UeXBlMSAvVHlwZSAvRm9udAo+PgplbmRvYmoKNiAwIG9iago8PAovQmFzZUZvbnQg
L1N5bWJvbCAvTmFtZSAvRjUgL1N1YnR5cGUgL1R5cGUxIC9UeXBlIC9Gb250Cj4+CmVuZG9iago3
IDAgb2JqCjw8Ci9Db250ZW50cyAxMSAwIFIgL01lZGlhQm94IFsgMCAwIDU5NS4yNzU2IDg0MS44
ODk4IF0gL1BhcmVudCAxMCAwIFIgL1Jlc291cmNlcyA8PAovRm9udCAxIDAgUiAvUHJvY1NldCBb
IC9QREYgL1RleHQgL0ltYWdlQiAvSW1hZ2VDIC9JbWFnZUkgXQo+PiAvUm90YXRlIDAgL1RyYW5z
IDw8Cgo+PiAKICAvVHlwZSAvUGFnZQo+PgplbmRvYmoKOCAwIG9iago8PAovUGFnZU1vZGUgL1Vz
ZU5vbmUgL1BhZ2VzIDEwIDAgUiAvVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKOSAwIG9iago8PAov
QXV0aG9yIChcKGFub255bW91c1wpKSAvQ3JlYXRpb25EYXRlIChEOjIwMjYxMDE1MTIxODA2KzAw
JzAwJykgL0NyZWF0b3IgKFwodW5zcGVjaWZpZWRcKSkgL0tleXdvcmRzICgpIC9Nb2REYXRlIChE
OjIwMjYxMDE1MTIxODA2KzAwJzAwJykgL1Byb2R1Y2VyIChSZXBvcnRMYWIgUERGIExpYnJhcnkg
LSBcKG9wZW5zb3VyY2VcKSkgCiAgL1N1YmplY3QgKFwodW5zcGVjaWZpZWRcKSkgL1RpdGxlIChc
KGFub255bW91c1wpKSAvVHJhcHBlZCAvRmFsc2UKPj4KZW5kb2JqCjEwIDAgb2JqCjw8Ci9Db3Vu
dCAxIC9LaWRzIFsgNyAwIFIgXSAvVHlwZSAvUGFnZXMKPj4KZW5kb2JqCjExIDAgb2JqCjw8Ci9G
aWx0ZXIgWyAvQVNDSUk4NURlY29kZSAvRmxhdGVEZWNvZGUgXSAvTGVuZ3RoIDE5ODQKPj4Kc3Ry
ZWFtCkdiITtkPWA8JVMmOlZzL1FxLWxWL0tWSywvL0RzYyJwbz4jRVYmNi1gRl4obltjSF5FR1E3
V2U6a3JVZF4mbWEpKV5EZF5jTEklcDMmOzZSJFU8RW9PKEpCISMxMz1vSkk8O1chRVZ0MmkhT2Rf
UEAjXU1QZEQxY1QnKElZXHIkZWVcWXQ7JE4lPDFaI0ZMVFhcZTpBRVtka1QwUz1pR1tIVTMhN29I
OFsyaj9YJ1djXXVKNk9yZlZvYG0/YTdUM1lmcj8xYEw1RSxrb2FHQk1HXyNEM2cwXVNGc0k4XTo5
KDVBZic+LThzJFVEaCpHJ1s+TidFLisyUmJuMSNqRF9wUGZGZmhnQ00oO2lyU1psImldSWNYTSEt
X043ZEU2dCVJRlVEWFYlbjw8Uik1ZGtYOUQ1ZG8oMmhsOTkmJmtVPllPNl8yQiNfaEp1aSVbZkly
X2tkLD5EOW9GZkZWY0MwNWkxMFs+LDViJy8jXjgqdSRJZCxiMSsuUEZoTyVAVSo2ITU2cXBZZihC
ODJOSEI3alojI085KiguOFk7QVgkWF9GVjtMbWReOS1WTVdoIk9eZ1ohOic6PydLOSRZKUQ/UUct
LUMkZSJZbGQ+bjUpUDdDJUpJcCQuVk81LjBUbl9MckNdKzlKNyc5JitGP2AhJmAtXEVzcXA8MjZH
Q0YmQXIzOCFXXFNNbEc+NGIjMVs4YytaY24iciJ1MFRsWWJyRF1wcSlBJlNWRCptb2olQUBWWWRw
KSRUdTdMJEFHIVU/ZlxEaDlPXGFjKDsuYFMhXjZfWTBEZWpQL0w8RCdhM2koS1pGKUtzIlphYSVn
MDA8Z1U5TGRQT2NQNnQpdGFOPUxCNlA/QV8rOzAtPVlTXS5zLlYxK3ExRk0iVV5eM3BFO0twQnFo
JmtESi4jSFVocytbY05OUiI+Xks0OWhuKDknOWU2VkdjbkEkKTVbO0FiMEQ+Ll1kXzVGUmxyWDtp
UE44XG9GOW9JZ2YjKVEtUyhYNz89YkRCYTpfO3E/cT1uajdYTClwUGJVLTMuaW8yJT9gRGlTRjBS
YzZLTDw5ZHRUITlwZTFPNzNGUWU/M0sjSCg0QkxKY3BXbFkpPmxVdFVhSy8sXmU9KzdmKTZrK1ll
bCZeJU9CWThfPkc3Iykocjk2OV9PI0I+Xz9WRUtgO2hmcklgckZfSVZgIV5RakZRLGZWblg4ZSRa
LDo8dUhQJD0zaDhtX0E6LD1kVyIkQGBkX2VTKkFFJGRYYFArUjNpKCNoIyY+OFcnSyRIN2w0SGoq
PV1KaztQR1tqdVVkMXAuTk5tczZQazFeaUBuNCcwWTBTWG1VZzM+T3BIOVVkQXFbInJLaUpNZ1Yu
ayJLYT1wJWRDJCQ8KThMRVJKL2EmX2ovP1MlW15fRldcVFwkcm1cMmgvPTVeaF1jWXEhXllrNiVm
U0AoYFNGPGRrUF1FLSRCPmBOKEZoPSZoPWEpTkwuXlMjS1AnbzNgMkZnZy5ec19IKE1zaSpyLUFd
JjgwMDInJ00kOCU/UlZjN0RMVnEpIiZBOlNxIyJVRypWI1dzSSwjN01iQVQpVzxOMy03R3NabVgx
SE5UcTJiTzEkSlM0QjYzKGBWW0JdL1NLaylcRi0mXHMrPE5lRWxNcy9RbGZEITtSLT9KSltbWEIr
bC45Pi9wNDxpN2AtLk8vY0NTamtDNz9hOl5MY2BhXCcqWFtfOFowSyRWcTVkYXUkWkldZGFSKlY7
UEVNLE4wQCEnWFtXYDlcNExjais9PSsvb0c8LSpuOkNibFJeOEE4ZzEzWEpTOFZARk8+ZmVZLj1F
RVNTP1dkOj09UG0tXlFJOT5BbSRLIURGLGRZaj9kQGs6dSgrLVMidFtJNWwtcERSXmhKaVxLN0Uz
WFZKakBRUlNESW1nPG5vbCU8PC1JMlc7Vk9tTyNKKTlqU1lTYmltW05QP1RTWyVvUjA3Lz9FYUFo
bGMvJD1XREcjajtJJ1BoY3JuRml1JzJuPTQ1O0RldVNnLWAoRFY+JDl0bk9pSXFiNl5sJiNoJlc+
Qi5gcj0vbV9mNjorYUk7ZkI2N0ZzK1g6N2AmViJzbzRzUlRpbjlfJyZLOlROXDBfaTtqPDxfRDN1
ciN0Z3U0QFlyP21XYF1gRT5qUFRWTloxPkMsMzoxYixIUzU6aClJdS81LVxRJiVJU1RQWlcpNj4p
XWhZaFVEUykxTUM7Yy0iUldLaWRvKCdGRjohY0IkXFdsJWlJJEF1O3BmZV47V19EbkYuMWtZVGZR
KCltL1NaZ01CPmRbPT5jSlZUMWJhOz0vUjhjVFptOk88PCMvXEg/U29tQFFnaD80aUVMLCY4X0o7
aCYkNS9BTTFmQ04xNDouV0hBJzJhX08vNV5SMFpcLllMdHJDLjFyPFkoOGY2IzIyJUliMS4pYihk
TnQlNHBaUTxlLENVIlpPKUo7XUhwbjNgWEAwMyZaYGVbPyVHcUQ6XzwsYG9oMkYmNU5xLV48YypQ
Xi01W0djbkBHN1NoTydsPU9eVk10dS0zJ1M3Z00xLDkqNldsS0g4SCFSJVhhJE5OUFNXYFBrXTJD
OU1iWFVKTm9mUkJda3RjZjgsW11LZFpDRz42THU4cEU+aDY/PE1YVSkmKHIlZG5Hfj5lbmRzdHJl
YW0KZW5kb2JqCnhyZWYKMCAxMgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwNjEgMDAwMDAg
biAKMDAwMDAwMDEzMiAwMDAwMCBuIAowMDAwMDAwMjM5IDAwMDAwIG4gCjAwMDAwMDAzNTEgMDAw
MDAgbiAKMDAwMDAwMDQzNCAwMDAwMCBuIAowMDAwMDAwNTQ5IDAwMDAwIG4gCjAwMDAwMDA2MjYg
MDAwMDAgbiAKMDAwMDAwMDgzMSAwMDAwMCBuIAowMDAwMDAwOTAwIDAwMDAwIG4gCjAwMDAwMDEx
ODAgMDAwMDAgbiAKMDAwMDAwMTI0MCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9JRCAKWzxjMjRmNDUy
ZWY1YjM4ZjUwMGM5NTVkNmJjMzQzMzEyMj48YzI0ZjQ1MmVmNWIzOGY1MDBjOTU1ZDZiYzM0MzMx
MjI+XQolIFJlcG9ydExhYiBnZW5lcmF0ZWQgUERGIGRvY3VtZW50IC0tIGRpZ2VzdCAob3BlbnNv
dXJjZSkKCi9JbmZvIDkgMCBSCi9Sb290IDggMCBSCi9TaXplIDEyCj4+CnN0YXJ0eHJlZgozMzE2
CiUlRU9GCg==
"""

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
        conn.execute("""CREATE TABLE IF NOT EXISTS resultats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve TEXT NOT NULL,
            niveau TEXT NOT NULL,
            notion TEXT NOT NULL,
            question TEXT NOT NULL,
            reponse TEXT NOT NULL,
            bonne_reponse TEXT NOT NULL,
            correct INTEGER NOT NULL,
            date_utc TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS preferences (
            cle TEXT PRIMARY KEY, valeur TEXT NOT NULL
        )""")


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
        conn.execute("""CREATE TABLE IF NOT EXISTS profils (
            nom TEXT PRIMARY KEY, niveau TEXT NOT NULL DEFAULT 'CE1',
            preferences_json TEXT NOT NULL DEFAULT '{}', cree_le TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS histoires (
            id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT NOT NULL,
            contenu TEXT NOT NULL, source TEXT NOT NULL, niveau TEXT NOT NULL,
            sons_cibles TEXT NOT NULL DEFAULT '', interets TEXT NOT NULL DEFAULT '',
            statut TEXT NOT NULL DEFAULT 'approuvee', cree_par TEXT NOT NULL,
            cree_le TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS historique_histoires (
            id INTEGER PRIMARY KEY AUTOINCREMENT, eleve TEXT NOT NULL,
            histoire_id INTEGER NOT NULL, proposee_le TEXT NOT NULL,
            FOREIGN KEY(histoire_id) REFERENCES histoires(id)
        )""")
        conn.execute("INSERT OR IGNORE INTO profils(nom,niveau,cree_le) VALUES(?,?,?)",
                     (lire_preference("eleve_actif", "Élève"), lire_preference("niveau_actif", "CE1"),
                      datetime.now().astimezone().isoformat(timespec="seconds")))
        conn.execute("""CREATE TABLE IF NOT EXISTS textes_personnalises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            contenu TEXT NOT NULL,
            niveau TEXT NOT NULL,
            sons_cibles TEXT NOT NULL DEFAULT '',
            cree_par TEXT NOT NULL,
            cree_le TEXT NOT NULL,
            modifie_le TEXT NOT NULL
        )""")


def generer_pdf_imprimable(titre, contenu, version="enfant", taille=20, interligne=1.5, notes=""):
    """Construit un vrai PDF A4 local avec ReportLab; aucune API externe requise."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors as pdfcolors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from xml.sax.saxutils import escape as xml_escape

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm, title=titre)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MathisBody", parent=styles["BodyText"],
                              fontName="Helvetica", fontSize=int(taille),
                              leading=int(taille*float(interligne)), textColor=pdfcolors.HexColor("#222222"),
                              spaceAfter=8))
    styles.add(ParagraphStyle(name="MathisTitle", parent=styles["Title"], fontSize=20, leading=25))
    story = [Paragraph(xml_escape(titre), styles["MathisTitle"]),
             Spacer(1, 5*mm),
             Paragraph(f"Version {xml_escape(version)} · {datetime.now().strftime('%d/%m/%Y')}",
                       styles["Italic"]), Spacer(1, 5*mm)]
    for ligne in contenu.splitlines():
        story.append(Paragraph(xml_escape(ligne) if ligne.strip() else "&#160;", styles["MathisBody"]))
    if notes and version == "adulte":
        story += [Spacer(1, 8*mm), Paragraph("Notes pour l’adulte", styles["Heading2"]),
                  Paragraph(xml_escape(notes).replace("\n", "<br/>"), styles["MathisBody"])]
    doc.build(story)
    return buffer.getvalue()


def html_imprimable(titre, contenu, version="enfant", couleurs=True, taille=20,
                    interligne=1.8, illustration=False, notes=""):
    """Génère une page HTML autonome, imprimable depuis le navigateur ou enregistrable en PDF."""
    safe_title = escape(titre)
    safe_content = escape(contenu).replace("\n", "<br>")
    notes_html = f"<section class='notes'><h2>Notes pour l'adulte</h2><p>{escape(notes)}</p></section>" if notes and version == "adulte" else ""
    css = """
    @page { size: A4; margin: 18mm; }
    body { font-family: Arial, 'Lexie Readable', sans-serif; color:#222; max-width: 850px;
           margin: 0 auto; font-size: %spx; line-height:%s; letter-spacing:.02em; }
    h1 { font-size:1.4em; } .meta { color:#555; font-size:.75em; border-bottom:1px solid #bbb;padding-bottom:8px; }
    .texte { white-space:normal; } .notes { border-top:1px solid #aaa; margin-top:2em; font-size:.8em; }
    .lignes { height:2.2em; border-bottom:1px solid #aaa; }
    @media print { .actions {display:none;} body{max-width:none;} }
    """ % (int(taille), float(interligne))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{safe_title}</title>
    <style>{css}</style></head><body><div class="actions"><button onclick="window.print()">Imprimer / Enregistrer en PDF</button></div>
    <h1>{safe_title}</h1><p class="meta">Version {escape(version)} · Générée le {datetime.now().strftime('%d/%m/%Y')}</p>
    <main class="texte">{safe_content}</main>{notes_html}</body></html>"""


def proposer_histoire(eleve, titre, contenu, source, niveau, sons="", interets="", statut="approuvee"):
    with connexion_db() as conn:
        cur = conn.execute("""INSERT INTO histoires(titre,contenu,source,niveau,sons_cibles,interets,statut,cree_par,cree_le)
        VALUES(?,?,?,?,?,?,?,?,?)""", (titre, contenu, source, niveau, sons, interets, statut, eleve,
        datetime.now().astimezone().isoformat(timespec="seconds")))
        return cur.lastrowid


def sons_couleurs_html(texte, activer=True):
    """Colorie les graphèmes connus sans confondre les terminaisons verbales muettes.

    Règle contextuelle importante : dans « ils/elles parlent », la terminaison
    verbale -ent est muette et ne doit pas être colorée comme le son nasal /ɑ̃/.
    La suite « ui » n'est pas ajoutée à la liste des graphèmes colorés : elle
    reste donc dans la couleur du texte, au lieu d'être assimilée à « eu ».
    """
    if not activer:
        return escape(texte).replace("\n", "<br>")

    couleurs = {
        "eau": lire_preference("couleur_o/au/eau", "#D4AC0D"),
        "ain": lire_preference("couleur_in/ain/ein", "#239B56"),
        "ein": lire_preference("couleur_in/ain/ein", "#239B56"),
        "oi": lire_preference("couleur_oi", "#222222"),
        "on": lire_preference("couleur_on", "#784212"),
        "un": lire_preference("couleur_un", "#922B21"),
        "ou": lire_preference("couleur_ou", "#E60000"),
        "an": lire_preference("couleur_an/en nasal", "#E67E22"),
        "en": lire_preference("couleur_an/en nasal", "#E67E22"),
        "au": lire_preference("couleur_o/au/eau", "#D4AC0D"),
        "ai": lire_preference("couleur_et/ez/er/ai/ei", "#7D3C98"),
        "ei": lire_preference("couleur_et/ez/er/ai/ei", "#7D3C98"),
        "et": lire_preference("couleur_et/ez/er/ai/ei", "#7D3C98"),
        "ez": lire_preference("couleur_et/ez/er/ai/ei", "#7D3C98"),
        "er": lire_preference("couleur_et/ez/er/ai/ei", "#7D3C98"),
        "eu": lire_preference("couleur_eu/œu", "#5DADE2"),
        "œu": lire_preference("couleur_eu/œu", "#5DADE2"),
        "ch": lire_preference("couleur_ch", "#CD8B62"),
        "qu": "#34495E",
        "in": lire_preference("couleur_in/ain/ein", "#239B56"),
    }

    # Repère les mots et leur contexte pour ne pas colorier -ent verbal.
    mots = list(re.finditer(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÆæ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿŒœÆæ]+)*", texte))
    terminaisons_ent_muettes = set()
    pronoms_sujets = {"ils", "elles"}
    verbes_frequents_ent = {
        "parlent", "mangent", "chantent", "jouent", "regardent", "écoutent",
        "marchent", "dansent", "aiment", "adorent", "arrivent", "partent",
        "restent", "tombent", "passent", "travaillent", "finissent",
        "choisissent", "grandissent", "prennent", "viennent", "font",
        "vont", "peuvent", "veulent", "doivent", "disent", "lisent",
        "écrivent", "courent", "dorment", "ouvrent", "offrent",
    }
    for idx, wm in enumerate(mots):
        mot = wm.group(0).lower()
        precedent = mots[idx - 1].group(0).lower() if idx > 0 else ""
        if mot.endswith("ent") and (
            precedent in pronoms_sujets or mot in verbes_frequents_ent
        ):
            terminaisons_ent_muettes.add((wm.start(), wm.end() - 3, wm.end()))

    pat = re.compile(r"eau|ain|ein|œu|ou|on|un|oi|an|en|au|ai|ei|et|ez|er|eu|ch|qu|in", re.I)
    out, pos = [], 0
    for m in pat.finditer(texte):
        token = m.group(0)
        token_lower = token.lower()

        # Si le graphème « en » appartient à la terminaison verbale muette -ent,
        # on le laisse en couleur normale.
        if token_lower == "en" and any(
            start_ent <= m.start() and m.end() <= end_ent
            for _, start_ent, end_ent in terminaisons_ent_muettes
        ):
            continue

        # « an/en » devant une voyelle correspond généralement à une suite de
        # voyelles prononcées séparément plutôt qu'au son nasal.
        if token_lower in {"an", "en"} and m.end() < len(texte) and texte[m.end()].lower() in "aeiouyàâäéèêëïîôöùûü":
            continue

        out.append(escape(texte[pos:m.start()]))
        color = couleurs.get(token_lower, "#222222")
        out.append(f'<span style="color:{color};font-weight:700">{escape(token)}</span>')
        pos = m.end()

    out.append(escape(texte[pos:]))
    return "".join(out).replace("\n", "<br>")


def decouper_en_graphemes(mot, graphemes_personnalises=None):
    """Découpe un mot en unités simples et graphèmes complexes, du plus long au plus court."""
    complexes = [g.strip().lower() for g in (graphemes_personnalises or []) if g.strip()]
    complexes = sorted(set(complexes + ["eau", "ain", "ein", "ch", "ou", "on", "an", "en", "oi", "un", "in", "au", "ai", "eu", "qu", "ph", "gn", "ill"]), key=len, reverse=True)
    mot_bas = mot.lower()
    blocs, i = [], 0
    while i < len(mot):
        trouve = next((g for g in complexes if mot_bas.startswith(g, i)), None)
        if trouve:
            blocs.append(mot[i:i+len(trouve)])
            i += len(trouve)
        else:
            blocs.append(mot[i])
            i += 1
    return blocs


def fabriquer_mots_a_trous(mots):
    """Chaque mot non vide a au moins un blanc; les graphèmes fréquents sont masqués en priorité."""
    graph = ("eau","ain","ein","ch","ou","on","an","en","oi","un","in","au","ai","eu","qu")
    resultats = []
    for mot in mots:
        m = mot.strip()
        if not m:
            continue
        bas = m.lower()
        masque = None
        for g in graph:
            idx = bas.find(g)
            while idx >= 0:
                fin = idx + len(g)
                if g in {"an", "en"} and fin < len(bas) and bas[fin] in "aeiouyàâäéèêëïîôöùûü":
                    idx = bas.find(g, idx + 1)
                    continue
                masque = m[:idx] + "__" + m[fin:]
                break
            if masque is not None:
                break
        if masque is None:
            lettres = [i for i,c in enumerate(m) if c.isalpha()]
            if lettres:
                i = lettres[len(lettres)//2]
                masque = m[:i] + "_" + m[i+1:]
            else:
                masque = "_" + m[1:] if len(m)>1 else "_"
        if "_" not in masque:
            masque = m[:1] + "_" + m[2:] if len(m)>2 else m[0] + "_"
        resultats.append((m, masque))
    return resultats


def lire_audio_navigateur(texte, key="audio"):
    """Lecture vocale via le navigateur, avec bouton de relecture; nécessite une voix française disponible."""
    payload = json.dumps(texte, ensure_ascii=False).replace("</", "<\\/")
    components.html(f'''<div style="font-family:Arial"><button id="play_{key}">🔊 Écouter / réécouter</button><button id="stop_{key}">⏹ Arrêter</button><script>
    const t = {payload};
    document.getElementById("play_{key}").onclick = () => {{ if (!window.speechSynthesis) {{ alert("La synthèse vocale n'est pas disponible dans ce navigateur."); return; }}
      window.speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.lang="fr-FR"; window.speechSynthesis.speak(u); }};
    document.getElementById("stop_{key}").onclick = () => window.speechSynthesis && window.speechSynthesis.cancel();
    </script></div>''', height=48)


def afficher_bibliotheque_histoires(eleve, niveau):
    st.title("📚 Bibliothèque d’histoires personnalisées")
    st.caption("Les histoires proposées à un enfant sont suivies séparément pour chaque profil. Une histoire IA reste en attente tant que l’adulte ne l’a pas validée.")
    with st.expander("➕ Ajouter un texte personnel", expanded=True):
        titre = st.text_input("Titre du texte", key="biblio_titre")
        contenu = st.text_area("Texte de l’adulte", height=180, key="biblio_texte")
        sons = st.text_input("Sons ou graphèmes à travailler (facultatif)", key="biblio_sons")
        interets = st.text_input("Centres d’intérêt (facultatif)", key="biblio_interets")
        if st.button("Enregistrer le texte personnel", key="biblio_save") and titre.strip() and contenu.strip():
            proposer_histoire(eleve, titre.strip(), contenu.strip(), "Texte fourni par l’adulte", niveau, sons, interets, "approuvee")
            st.success("Texte ajouté à la bibliothèque.")
            st.rerun()
    st.divider()
    st.subheader("✨ Créer une histoire avec l’IA (validation adulte obligatoire)")
    c1,c2 = st.columns(2)
    with c1:
        theme = st.text_input("Thème", key="biblio_theme")
        niveau_h = st.selectbox("Niveau de lecture", ["CP","CE1","CE2","CM1","CM2"], index=["CP","CE1","CE2","CM1","CM2"].index(niveau) if niveau in ["CP","CE1","CE2","CM1","CM2"] else 1, key="biblio_niveau")
    with c2:
        interets_ia = st.text_input("Intérêts de l’enfant", key="biblio_interets_ia")
        sons_ia = st.text_input("Sons à cibler", key="biblio_sons_ia")
    if st.button("Générer une proposition à relire", key="biblio_gen") and theme.strip():
        prompt = (f"Écris une histoire originale en français pour un enfant de niveau {niveau_h}, thème {theme!r}. "
                  f"Centres d'intérêt: {interets_ia or 'non précisés'}. Sons/graphèmes à travailler: {sons_ia or 'non précisés'}. "
                  "Vocabulaire accessible, phrases courtes, environ 150 à 250 mots. Donne uniquement le titre sur la première ligne puis l'histoire.")
        with st.spinner("Préparation de l'histoire…"):
            proposition = interroger_ia(prompt, temperature=0.75)
        lignes = proposition.splitlines()
        titre_ia = lignes[0].strip().lstrip("# ")[:100] if lignes else theme
        texte_ia = "\n".join(lignes[1:]).strip() if len(lignes)>1 else proposition
        if proposition.startswith("Erreur IA"):
            st.error(proposition)
        else:
            proposer_histoire(eleve, titre_ia or theme, texte_ia or proposition, "Générée par IA", niveau_h, sons_ia, interets_ia, "a_valider")
            st.success("Proposition enregistrée en attente de validation adulte.")
            st.rerun()
    with connexion_db() as conn:
        histoires = [dict(r) for r in conn.execute("SELECT * FROM histoires ORDER BY id DESC").fetchall()]
    st.subheader("Histoires à valider")
    en_attente = [h for h in histoires if h["statut"] == "a_valider"]
    if not en_attente:
        st.caption("Aucune proposition en attente.")
    for h in en_attente:
        with st.expander(f"🔎 {h['titre']} — {h['source']}"):
            st.write(h["contenu"])
            if st.button("✅ Approuver pour la bibliothèque", key=f"approve_{h['id']}"):
                with connexion_db() as conn:
                    conn.execute("UPDATE histoires SET statut='approuvee' WHERE id=?", (h["id"],))
                st.rerun()
            if st.button("🗑️ Refuser cette proposition", key=f"reject_{h['id']}"):
                with connexion_db() as conn:
                    conn.execute("DELETE FROM histoires WHERE id=?", (h["id"],))
                st.rerun()
    disponibles = [h for h in histoires if h["statut"] == "approuvee"]
    st.subheader("Histoires disponibles")
    if not disponibles:
        st.info("Ajoute un texte ou approuve une histoire pour constituer la bibliothèque.")
    for h in disponibles:
        with st.expander(f"📖 {h['titre']} · {h['niveau']} · {h['source']}"):
            deja = False
            with connexion_db() as conn:
                deja = conn.execute("SELECT 1 FROM historique_histoires WHERE eleve=? AND histoire_id=? LIMIT 1", (eleve,h["id"])).fetchone() is not None
            st.markdown(sons_couleurs_html(h["contenu"], st.checkbox("Afficher le code couleur des sons", value=True, key=f"story_colors_{h['id']}")), unsafe_allow_html=True)
            if st.checkbox("Activer l’audio phrase par phrase", value=False, key=f"story_audio_{h['id']}"):
                phrases_audio = [x.strip() for x in re.split(r"(?<=[.!?])\s+", h["contenu"]) if x.strip()]
                for no, phrase_audio in enumerate(phrases_audio, 1):
                    st.caption(f"Phrase {no} / {len(phrases_audio)}")
                    lire_audio_navigateur(phrase_audio, key=f"story{h['id']}p{no}")
            if deja:
                st.info("Cette histoire a déjà été proposée à ce profil. Elle reste consultable et réimprimable par l’adulte.")
            col1,col2 = st.columns(2)
            with col1:
                if st.button("📘 Marquer comme proposée à cet enfant", key=f"story_offer_{h['id']}", disabled=deja):
                    with connexion_db() as conn:
                        conn.execute("INSERT INTO historique_histoires(eleve,histoire_id,proposee_le) VALUES(?,?,?)",
                                     (eleve,h["id"],datetime.now().astimezone().isoformat(timespec="seconds")))
                    st.success("Historique mis à jour pour ce profil.")
                    st.rerun()
            with col2:
                html = html_imprimable(h["titre"], h["contenu"], "enfant", True, 22, 1.8)
                st.download_button("🖨️ Version enfant imprimable", html, file_name=f"histoire_{h['id']}.html", mime="text/html", key=f"story_print_{h['id']}")
            taille_h = st.slider("Taille du texte imprimé", 16, 32, 22, key=f"story_size_{h['id']}")
            interligne_h = st.slider("Espacement des lignes", 1.3, 3.0, 1.8, 0.1, key=f"story_space_{h['id']}")
            questions = st.text_area("Questions de compréhension (facultatif)", key=f"story_questions_{h['id']}", placeholder="1. Qui est le personnage ?\\n2. Que se passe-t-il ?")
            notes_adulte = st.text_area("Notes/correction pour l’adulte (facultatif)", key=f"story_notes_{h['id']}")
            contenu_enfant = h["contenu"] + (("\\n\\nQuestions :\\n" + questions) if questions.strip() else "")
            st.download_button("📄 PDF enfant", generer_pdf_imprimable(h["titre"], contenu_enfant, "enfant", taille_h, interligne_h),
                               file_name=f"histoire_{h['id']}_enfant.pdf", mime="application/pdf", key=f"story_pdf_child_{h['id']}")
            st.download_button("🔐 PDF adulte avec notes", generer_pdf_imprimable(h["titre"], h["contenu"], "adulte", taille_h, interligne_h, notes_adulte),
                               file_name=f"histoire_{h['id']}_adulte.pdf", mime="application/pdf", key=f"story_pdf_adult_{h['id']}")
            st.caption("Le PDF est généré localement. La version HTML permet aussi d’utiliser la boîte d’impression du navigateur.")


def afficher_atelier_dictee(eleve, niveau):
    st.title("🎤 Atelier de dictée en 4 étapes")
    st.write("La séquence est générée à partir des mots saisis. Vérifie les propositions avant impression : les aides phonétiques sont indicatives et le contexte compte.")
    raw = st.text_area("Mots de la semaine (séparés par virgules, espaces ou retours à la ligne)", height=100,
                       placeholder="chat, boucle, Mathis, ananas, bateau", key="atelier_mots")
    titre = st.text_input("Titre de la fiche", value="Dictée de la semaine", key="atelier_titre")
    couleurs = st.checkbox("Activer le code couleur des sons", True, key="atelier_couleurs")
    hints = st.checkbox("Afficher les indices de prononciation", True, key="atelier_hints")
    taille = st.slider("Taille de police pour impression", 16, 32, 22, key="atelier_taille")
    espacement = st.slider("Interligne pour impression", 1.3, 3.0, 1.9, 0.1, key="atelier_interligne")
    mots = [m.strip(" .;") for m in re.split(r"[,;\s]+", raw) if m.strip(" .;")]
    if mots:
        st.subheader("Étape 1 — Découvrir les mots")
        st.markdown(sons_couleurs_html(" · ".join(mots), couleurs), unsafe_allow_html=True)
        if hints:
            st.caption("Indices possibles : ch → /ʃ/ ; ou → /u/ ; oi → /wa/ ; qu → /k/. Les lettres muettes et les sons nasaux dépendent du mot.")
        st.subheader("Étape 2 — Lettres et graphèmes à découper")
        st.markdown("Chaque graphème complexe sélectionné est conservé comme une seule étiquette (par exemple **ou**, **on**, **ch**, **eau**). Vérifie les découpages proposés avant utilisation : certains sons dépendent du mot.")
        graphèmes = st.text_input("Graphèmes à traiter comme des unités (facultatif)", value="ou, on, ch, an, en, oi, eau, qu", key="atelier_graph")
        liste_graphèmes = [g.strip() for g in graphèmes.split(",") if g.strip()]
        lignes_cartes = [f"{m} : " + "   ✂   ".join(f"[ {bloc} ]" for bloc in decouper_en_graphemes(m, liste_graphèmes)) for m in mots]
        cartes = "\n\n".join(lignes_cartes)
        st.code(cartes)
        st.subheader("Étape 3 — Mots à trous (chaque mot comporte au moins un blanc)")
        trous = fabriquer_mots_a_trous(mots)
        st.markdown(sons_couleurs_html("   ·   ".join(t for _,t in trous), couleurs), unsafe_allow_html=True)
        st.subheader("Étape 4 — Dictée finale et correction adulte")
        phrases = st.text_area("Texte de la dictée (facultatif ; sinon liste de mots)", value=" ".join(mots), height=100, key="atelier_texte_final")
        notes = st.text_area("Notes/corrections pour l’adulte", key="atelier_notes")
        enfant = titre + "\n\n" + phrases + "\n\n" + "\n".join("____________________________________________" for _ in range(max(3,len(mots))))
        adulte = titre + "\\n\\nDictée complète :\\n" + phrases + "\\n\\nMots cibles : " + ", ".join(mots) + "\\n\\nNotes : " + notes
        c1,c2,c3 = st.columns(3)
        with c1:
            st.download_button("📄 PDF — version enfant", generer_pdf_imprimable(titre, enfant, "enfant", taille, espacement),
                               file_name="dictee_enfant.pdf", mime="application/pdf", key="atelier_pdf_enfant")
            st.download_button("🖨️ Version enfant imprimable", html_imprimable(titre, enfant, "enfant", couleurs, taille, espacement),
                               file_name="dictee_enfant.html", mime="text/html", key="atelier_dl_enfant")
        with c2:
            st.download_button("🔐 PDF — version adulte", generer_pdf_imprimable(titre, adulte, "adulte", taille, espacement, notes),
                               file_name="dictee_adulte.pdf", mime="application/pdf", key="atelier_pdf_adulte")
            st.download_button("🖨️ Version adulte imprimable", html_imprimable(titre, adulte, "adulte", couleurs, taille, espacement, notes=notes),
                               file_name="dictee_adulte.html", mime="text/html", key="atelier_dl_adulte")
        with c3:
            cartes_texte = cartes.replace("✂", "\\n✂\\n")
            st.download_button("✂️ PDF — étiquettes à découper", generer_pdf_imprimable("Étiquettes à découper", cartes_texte, "enfant", taille, espacement),
                               file_name="etiquettes_dictee.pdf", mime="application/pdf", key="atelier_pdf_cartes")
            st.download_button("🖨️ Étiquettes imprimables", html_imprimable("Étiquettes à découper", cartes_texte, "enfant", couleurs, taille, espacement),
                               file_name="etiquettes_dictee.html", mime="text/html", key="atelier_dl_cartes")
        st.caption("Pour obtenir un PDF : ouvre le fichier HTML téléchargé, clique sur Imprimer, puis choisis « Enregistrer au format PDF ». L'impression directe dépend du navigateur.")


def afficher_reglages_dys():
    st.title("🎨 Réglages DYS et code couleur")
    st.subheader("👤 Profils enregistrés")
    with connexion_db() as conn:
        profils = [dict(r) for r in conn.execute("SELECT * FROM profils ORDER BY nom COLLATE NOCASE").fetchall()]
    if profils:
        st.dataframe([{"Profil": x["nom"], "Niveau": x["niveau"], "Créé le": x["cree_le"][:10]} for x in profils], use_container_width=True, hide_index=True)
    with st.form("form_nouveau_profil"):
        nouveau_nom = st.text_input("Créer un profil enfant (prénom ou pseudonyme)", max_chars=40)
        nouveau_niveau = st.selectbox("Niveau du nouveau profil", ["CP", "CE1", "CE2", "CM1", "CM2", "Collège", "Adulte"], index=1)
        if st.form_submit_button("➕ Enregistrer ce profil") and nouveau_nom.strip():
            with connexion_db() as conn:
                conn.execute("INSERT INTO profils(nom,niveau,cree_le) VALUES(?,?,?) ON CONFLICT(nom) DO UPDATE SET niveau=excluded.niveau", (nouveau_nom.strip(), nouveau_niveau, datetime.now().astimezone().isoformat(timespec="seconds")))
            st.success("Profil enregistré. Pour l’activer, sélectionne ce prénom dans le profil de la barre latérale.")
            st.rerun()
    st.write("Les réglages ci-dessous sont enregistrés localement. Le code couleur d'origine est conservé ; les couleurs personnalisées s'appliquent aux nouveaux supports utilisant le moteur complémentaire.")
    valeurs = {
        "oi":"#222222", "on":"#784212", "un":"#922B21", "ou":"#E60000",
        "an/en nasal":"#E67E22", "o/au/eau":"#D4AC0D", "et/ez/er/ai/ei":"#7D3C98",
        "eu/œu":"#5DADE2", "in/ain/ein":"#239B56", "ch":"#CD8B62", "lettres muettes":"#A6A6A6"
    }
    with st.form("form_reglages_dys"):
        couleurs = {}
        for nom, defaut in valeurs.items():
            couleurs[nom] = st.color_picker(nom, value=lire_preference("couleur_"+nom, defaut))
        activer_couleurs = st.checkbox("Activer le code couleur par défaut", value=lire_preference("sons_couleurs_actifs","1")=="1")
        activer_audio = st.checkbox("Afficher les commandes audio quand disponibles", value=lire_preference("sons_audio_actifs","1")=="1")
        activer_indices = st.checkbox("Afficher les indices de prononciation", value=lire_preference("sons_indices_actifs","1")=="1")
        if st.form_submit_button("💾 Enregistrer les réglages"):
            for nom, val in couleurs.items():
                enregistrer_preference("couleur_"+nom, val)
            enregistrer_preference("sons_couleurs_actifs", "1" if activer_couleurs else "0")
            enregistrer_preference("sons_audio_actifs", "1" if activer_audio else "0")
            enregistrer_preference("sons_indices_actifs", "1" if activer_indices else "0")
            st.success("Réglages enregistrés sur cet appareil.")



def texte_personnalise_html(titre, contenu, version="enfant", couleurs=True, taille=22,
                            interligne=1.8, sons_cibles="", questions="", notes=""):
    """Page HTML autonome pour impression locale, sans envoi de données à un service externe."""
    titre_s = escape(titre)
    contenu_html = sons_couleurs_html(contenu, activer=couleurs)
    questions_html = ""
    if questions.strip():
        questions_html = "<h2>Questions de compréhension</h2><p>" + escape(questions).replace("\n", "<br>") + "</p>"
    notes_html = ""
    if version == "adulte" and notes.strip():
        notes_html = "<section class='notes'><h2>Notes et correction adulte</h2><p>" + escape(notes).replace("\n", "<br>") + "</p></section>"
    sons_html = f"<p class='meta'>Sons ciblés : {escape(sons_cibles or 'non précisés')}</p>" if sons_cibles else ""
    css = f"""
    @page {{ size:A4; margin:18mm; }}
    body {{ font-family:Arial,sans-serif; color:#222; max-width:850px; margin:0 auto;
      font-size:{int(taille)}px; line-height:{float(interligne)}; letter-spacing:.02em; }}
    h1 {{font-size:1.4em}} h2 {{font-size:1em}} .meta {{font-size:.72em;color:#555;border-bottom:1px solid #bbb;padding-bottom:8px}}
    .texte {{margin-top:1em}} .notes {{border-top:1px solid #aaa;margin-top:2em;font-size:.8em}}
    .reponses {{margin-top:2em}} .ligne {{height:2em;border-bottom:1px solid #aaa}}
    @media print {{ .actions {{display:none}} body {{max-width:none}} }}
    """
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{titre_s}</title><style>{css}</style></head>
    <body><div class='actions'><button onclick='window.print()'>Imprimer / Enregistrer en PDF</button></div>
    <h1>{titre_s}</h1><p class='meta'>Version {escape(version)} · {datetime.now().strftime('%d/%m/%Y')}</p>{sons_html}
    <main class='texte'>{contenu_html}</main>{questions_html}{notes_html}</body></html>"""


def afficher_textes_personnalises(eleve, niveau):
    st.title("📝 Mes textes personnalisés")
    st.caption("Saisis, colle ou importe un texte. Il reste enregistré localement. Les activités sont créées à partir de ton texte : aucune IA n'est appelée automatiquement.")
    with connexion_db() as conn:
        textes = [dict(r) for r in conn.execute(
            "SELECT * FROM textes_personnalises ORDER BY modifie_le DESC, id DESC").fetchall()]
    choix = {f"{t['titre']} — {t['niveau']} · modifié le {t['modifie_le'][:10]} (#{t['id']})": t for t in textes}
    selection_label = st.selectbox("Textes déjà enregistrés", ["➕ Nouveau texte"] + list(choix), key="textes_perso_selection")
    selection = choix.get(selection_label)
    if selection and st.button("📂 Charger ce texte dans le formulaire", key="textes_perso_charger"):
        st.session_state["texte_perso_titre"] = selection["titre"]
        st.session_state["texte_perso_contenu"] = selection["contenu"]
        st.session_state["texte_perso_niveau"] = selection["niveau"]
        st.session_state["texte_perso_sons"] = selection["sons_cibles"]
        st.session_state["texte_perso_notes"] = ""
        st.rerun()
    uploaded = st.file_uploader("Importer un fichier texte (.txt)", type=["txt"], key="texte_perso_upload")
    if uploaded and st.button("Importer le contenu du fichier dans le champ", key="texte_perso_importer"):
        raw_bytes = uploaded.getvalue()
        try:
            imported = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            imported = raw_bytes.decode("cp1252", errors="replace")
        st.session_state["texte_perso_contenu"] = imported
        if not st.session_state.get("texte_perso_titre"):
            st.session_state["texte_perso_titre"] = Path(uploaded.name).stem
        st.success("Texte importé dans le formulaire. Vérifie-le puis enregistre-le.")
        st.rerun()

    with st.form("form_texte_personnalise", clear_on_submit=False):
        titre = st.text_input("Titre", key="texte_perso_titre", placeholder="Ex. : La promenade de Mathis")
        niveau_texte = st.selectbox("Niveau de lecture", ["CP", "CE1", "CE2", "CM1", "CM2", "Collège", "Adulte"],
                                    index=["CP", "CE1", "CE2", "CM1", "CM2", "Collège", "Adulte"].index(st.session_state.get("texte_perso_niveau", niveau))
                                    if st.session_state.get("texte_perso_niveau", niveau) in ["CP", "CE1", "CE2", "CM1", "CM2", "Collège", "Adulte"] else 1,
                                    key="texte_perso_niveau")
        sons = st.text_input("Sons/graphèmes à travailler (facultatif)", key="texte_perso_sons",
                             placeholder="Ex. : ou, on, ch, oi")
        contenu = st.text_area("Colle ou saisis ton texte ici", key="texte_perso_contenu", height=240,
                               placeholder="Tu peux saisir un texte scolaire, une histoire, une leçon ou quelques phrases.")
        if st.form_submit_button("💾 Enregistrer ce texte"):
            if not titre.strip() or not contenu.strip():
                st.error("Ajoute un titre et le contenu du texte avant de l'enregistrer.")
            else:
                now = datetime.now().astimezone().isoformat(timespec="seconds")
                if selection:
                    with connexion_db() as conn:
                        conn.execute("UPDATE textes_personnalises SET titre=?, contenu=?, niveau=?, sons_cibles=?, modifie_le=? WHERE id=?",
                                     (titre.strip(), contenu.strip(), niveau_texte, sons.strip(), now, selection["id"]))
                    st.success("Texte enregistré : la version sélectionnée a été mise à jour.")
                else:
                    with connexion_db() as conn:
                        conn.execute("INSERT INTO textes_personnalises(titre,contenu,niveau,sons_cibles,cree_par,cree_le,modifie_le) VALUES(?,?,?,?,?,?,?)",
                                     (titre.strip(), contenu.strip(), niveau_texte, sons.strip(), eleve,
                                      now, now))
                    st.success("Nouveau texte enregistré localement.")
                st.rerun()

    contenu_actuel = st.session_state.get("texte_perso_contenu", "").strip()
    titre_actuel = st.session_state.get("texte_perso_titre", "").strip() or "Mon texte"
    sons_actuels = st.session_state.get("texte_perso_sons", "").strip()
    if contenu_actuel:
        st.divider()
        st.subheader("Aperçu et activités à partir de ce texte")
        couleur_active = st.checkbox("Afficher le code couleur des sons", value=True, key="texte_perso_couleurs")
        st.markdown(sons_couleurs_html(contenu_actuel, couleur_active), unsafe_allow_html=True)
        st.caption("Le code couleur est une aide visuelle indicative : vérifie les mots ambigus et les lettres muettes avant de l'utiliser.")
        if st.checkbox("🔊 Activer l'écoute phrase par phrase", value=False, key="texte_perso_audio"):
            phrases = [x.strip() for x in re.split(r"(?<=[.!?])\s+", contenu_actuel) if x.strip()]
            for i, phrase in enumerate(phrases, 1):
                st.caption(f"Phrase {i} / {len(phrases)}")
                lire_audio_navigateur(phrase, key=f"texteperso_{hashlib.md5((titre_actuel+str(i)).encode()).hexdigest()[:8]}")
        questions = st.text_area("Questions de compréhension (facultatif)", key="texte_perso_questions",
                                 placeholder="1. Qui est le personnage ?\n2. Où se déroule l'histoire ?")
        notes = st.text_area("Notes ou correction pour l'adulte (facultatif)", key="texte_perso_notes")
        st.markdown("**Texte à trous** — les mots sont proposés avec un espace à compléter :")
        mots = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", contenu_actuel, flags=re.UNICODE)
        trous = fabriquer_mots_a_trous(mots) if mots else []
        texte_trous = "   ·   ".join(t for _, t in trous)
        st.text_area("Version d'entraînement à compléter", value=texte_trous, height=120, key="texte_perso_trous", disabled=True)
        taille = st.slider("Taille de police à l'impression", 16, 32, 22, key="texte_perso_taille")
        interligne = st.slider("Espacement des lignes", 1.3, 3.0, 1.8, 0.1, key="texte_perso_interligne")
        contenu_enfant = contenu_actuel + (("\n\nQuestions de compréhension :\n" + questions) if questions.strip() else "")
        contenu_adulte = contenu_actuel + "\n\nVersion de correction adulte — texte de référence.\n" + ("Questions :\n" + questions + "\n" if questions.strip() else "") + ("Notes :\n" + notes if notes.strip() else "")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("📄 PDF enfant", generer_pdf_imprimable(titre_actuel, contenu_enfant, "enfant", taille, interligne),
                               file_name="texte_personnalise_enfant.pdf", mime="application/pdf", key="texte_perso_pdf_enfant")
            html_enfant = texte_personnalise_html(titre_actuel, contenu_enfant, "enfant", couleur_active, taille, interligne, sons_actuels)
            st.download_button("🖨️ HTML enfant couleur", html_enfant, file_name="texte_personnalise_enfant.html", mime="text/html", key="texte_perso_html_enfant")
        with col2:
            st.download_button("🔐 PDF adulte", generer_pdf_imprimable(titre_actuel, contenu_adulte, "adulte", taille, interligne, notes),
                               file_name="texte_personnalise_adulte.pdf", mime="application/pdf", key="texte_perso_pdf_adulte")
            html_adulte = texte_personnalise_html(titre_actuel, contenu_adulte, "adulte", couleur_active, taille, interligne, sons_actuels, notes=notes)
            st.download_button("🖨️ HTML adulte couleur", html_adulte, file_name="texte_personnalise_adulte.html", mime="text/html", key="texte_perso_html_adulte")
        with col3:
            st.download_button("📝 Télécharger les mots à trous", generer_pdf_imprimable(titre_actuel + " — mots à trous", texte_trous, "enfant", taille, interligne),
                               file_name="texte_personnalise_mots_a_trous.pdf", mime="application/pdf", key="texte_perso_pdf_trous")
            st.download_button("⬛ Version noir et blanc", texte_personnalise_html(titre_actuel, contenu_enfant, "enfant", False, taille, interligne, sons_actuels),
                               file_name="texte_personnalise_noir_blanc.html", mime="text/html", key="texte_perso_nb")
        if selection and st.button("🗑️ Supprimer ce texte enregistré", key="texte_perso_supprimer"):
            with connexion_db() as conn:
                conn.execute("DELETE FROM textes_personnalises WHERE id=?", (selection["id"],))
            st.success("Texte supprimé.")
            st.rerun()


initialiser_db()
initialiser_extensions()

# --- MENU LATÉRAL PRINCIPAL ---
st.sidebar.title("📌 Navigation")
menu_selection = st.sidebar.radio(
    "Choisissez un module :",
    [
        "🏠 Présentation",
        "📄 Aide à la lecture (Texte & OCR)",
        "✨ Générateur d’histoires",
        "🎤 Aide à la dictée",
        "📐 Grammaire Visuelle & Accords",
        "🎯 Entraînement interactif",
        "📊 Mes progrès",
        "⚙️ Profil & sauvegarde",
        "📚 Bibliothèque d’histoires",
        "📝 Mes textes personnalisés",
        "🎤 Atelier de dictée complet",
        "🎨 Réglages DYS et code couleur"
    ]
)


with st.sidebar.expander("👤 Profils des élèves", expanded=True):
    niveaux_disponibles = ["CP", "CE1", "CE2", "CM1", "CM2", "Collège", "Adulte"]
    with connexion_db() as conn:
        profils_sidebar = [dict(r) for r in conn.execute("SELECT nom, niveau FROM profils ORDER BY nom COLLATE NOCASE").fetchall()]
    if not profils_sidebar:
        nom_initial = lire_preference("eleve_actif", "Élève").strip() or "Élève"
        niveau_initial = lire_preference("niveau_actif", "CE1")
        with connexion_db() as conn:
            conn.execute("INSERT OR IGNORE INTO profils(nom,niveau,cree_le) VALUES(?,?,?)", (nom_initial, niveau_initial, datetime.now().astimezone().isoformat(timespec="seconds")))
        profils_sidebar = [{"nom": nom_initial, "niveau": niveau_initial}]
    noms_profils = [p["nom"] for p in profils_sidebar]
    profil_memorise = lire_preference("eleve_actif", noms_profils[0])
    if profil_memorise not in noms_profils:
        profil_memorise = noms_profils[0]
    index_profil = noms_profils.index(profil_memorise)
    eleve_actif = st.selectbox("Profil actif", noms_profils, index=index_profil, key="profil_selection_actif")
    profil_courant = next((p for p in profils_sidebar if p["nom"] == eleve_actif), profils_sidebar[0])
    niveau_profil = profil_courant.get("niveau", "CE1")
    if niveau_profil not in niveaux_disponibles:
        niveau_profil = "CE1"
    niveau_actif = st.selectbox("Niveau de ce profil", niveaux_disponibles,
                                index=niveaux_disponibles.index(niveau_profil), key=f"profil_niveau_{eleve_actif}")
    if st.button("💾 Enregistrer les réglages du profil actif", use_container_width=True, key="profil_sauvegarder_actif"):
        with connexion_db() as conn:
            conn.execute("UPDATE profils SET niveau=? WHERE nom=?", (niveau_actif, eleve_actif))
        enregistrer_preference("eleve_actif", eleve_actif)
        enregistrer_preference("niveau_actif", niveau_actif)
        st.success(f"Profil « {eleve_actif} » enregistré.")
        st.rerun()
    with st.form("form_creer_profil_sidebar", clear_on_submit=True):
        st.markdown("**➕ Créer un autre profil**")
        nouveau_profil_nom = st.text_input("Prénom ou pseudonyme", max_chars=40, key="nouveau_profil_nom_sidebar")
        nouveau_profil_niveau = st.selectbox("Niveau initial", niveaux_disponibles, index=1, key="nouveau_profil_niveau_sidebar")
        creer_profil = st.form_submit_button("Créer et enregistrer le profil", use_container_width=True)
    if creer_profil:
        nom_nettoye = nouveau_profil_nom.strip()
        if not nom_nettoye:
            st.warning("Saisis un prénom ou un pseudonyme pour créer le profil.")
        elif nom_nettoye.casefold() in {n.casefold() for n in noms_profils}:
            st.warning("Un profil porte déjà ce nom. Choisis un autre prénom ou pseudonyme.")
        else:
            with connexion_db() as conn:
                conn.execute("INSERT INTO profils(nom,niveau,cree_le) VALUES(?,?,?)", (nom_nettoye, nouveau_profil_niveau, datetime.now().astimezone().isoformat(timespec="seconds")))
            enregistrer_preference("eleve_actif", nom_nettoye)
            enregistrer_preference("niveau_actif", nouveau_profil_niveau)
            st.success(f"Profil « {nom_nettoye} » créé.")
            st.rerun()
    # Le changement de profil est mémorisé ; les résultats et l’historique d’histoires sont filtrés par nom.
    enregistrer_preference("eleve_actif", eleve_actif)
    enregistrer_preference("niveau_actif", niveau_actif)


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
    'on': ('#6E2C00', 'on'),  # Code couleur de référence : marron
    'un': ('#B9770E', 'un'),
    'ou': ('#FF0000', 'ou'),  # Code couleur de référence : rouge
    'an': ('#E67E22', 'an'),  # Code couleur de référence : orange
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
    """
    Renvoie, pour chaque mot, un découpage syllabique (ex. « mai-son »).
    Si l'IA ne répond pas correctement, utilise un comptage de secours au lieu
    de traiter automatiquement chaque mot comme une seule syllabe.
    """
    import re
    import unicodedata

    decoupages_fixes = {
        "bonjour": "bon-jour",
        "banane": "ba-na-ne",
        "j’aime": "j’ai-me",
        "j'aime": "j'ai-me",
        "ecole": "é-co-le",
        "école": "é-co-le",
        "vacances": "va-can-ces",
        "voiture": "voi-ture",
        "maison": "mai-son",
        "appelle": "ap-pel-le",
        "m’appelle": "m’ap-pel-le",
        "m'appelle": "m'ap-pel-le",
        "connaissais": "con-nais-sais",
        "parti": "par-ti",
    }

    def nettoyer_mot(mot):
        mot = mot.strip(".,;:?!¡¿'’\\«»\"()[]{} ")
        return mot.lower()

    mots = []
    for brut in texte.lower().split():
        mot = nettoyer_mot(brut)
        if mot and mot not in mots:
            mots.append(mot)

    syllables_map = {}
    mots_a_analyser = []
    for mot in mots:
        if mot in decoupages_fixes:
            syllables_map[mot] = decoupages_fixes[mot]
        else:
            mots_a_analyser.append(mot)

    if mots_a_analyser:
        prompt = f"""
Pour chacun des mots français ci-dessous, sépare les syllabes de lecture avec un tiret.
Garde exactement le mot avant les deux-points et réponds avec une ligne par mot.
N'ajoute aucune explication.
Exemple :
maison:mai-son
banane:ba-na-ne
Mots :
{", ".join(mots_a_analyser)}
"""
        try:
            reponse = interroger_ia(prompt, temperature=0.0)
            for ligne in (reponse or "").splitlines():
                if ":" not in ligne:
                    continue
                mot_reponse, decoupe = ligne.split(":", 1)
                mot_reponse = nettoyer_mot(mot_reponse)
                decoupe = decoupe.strip().strip("`* ")
                # N'accepter que les découpages contenant le mot et des segments non vides.
                segments = [seg.strip() for seg in decoupe.split("-")]
                if (mot_reponse in mots_a_analyser and len(segments) >= 2
                        and all(segments)
                        and "".join(segments).replace("’", "'").replace("'", "")
                        == mot_reponse.replace("’", "'").replace("'", "")):
                    syllables_map[mot_reponse] = "-".join(segments)
        except Exception:
            # Le comptage de secours ci-dessous garde l'application fonctionnelle
            # lorsque l'API n'est pas configurée ou indisponible.
            pass

    for mot in mots:
        if mot not in syllables_map:
            syllables_map[mot] = count_syllables_approx(mot)

    return syllables_map


def count_syllables_approx(word):
    """
    Comptage de secours pour les arcs syllabiques.
    Il compte les noyaux vocaliques et traite les groupes de voyelles français
    comme un seul noyau. Ce n'est qu'une approximation : les syllabes de lecture
    exactes sont préférablement fournies par le découpage IA ou le dictionnaire.
    """
    import re

    clean_w = word.lower().strip(".,;:?!¡¿'’\\«»\"()[]{} ")
    if not clean_w:
        return 1

    # Les mots avec apostrophe sont comptés partie par partie : l'élision ne doit
    # pas fusionner artificiellement les voyelles des deux côtés de l'apostrophe.
    parties = [p for p in re.split(r"['’]", clean_w) if p]
    if not parties:
        return 1

    groupes_voyelles = (
        "eau", "oeu", "œu", "au", "ai", "ei", "eu", "ou", "oi", "ui",
        "an", "am", "en", "em", "on", "om", "in", "im", "ain", "aim",
        "ein", "ien", "oin", "un", "um", "é", "è", "ê"
    )
    voyelles = "aeiouyàâäéèêëïîôöùûüÿœæ"
    total = 0

    for partie in parties:
        if not partie:
            continue
        # Retirer le e final muet uniquement si le mot contient déjà un autre
        # noyau vocalique ; les mots connus comme « banane » sont traités plus
        # précisément par le dictionnaire fixe ci-dessus.
        p = partie
        if len(p) > 2 and p.endswith("e") and not p.endswith(("ée", "ie", "ue", "oe", "ye")):
            p = p[:-1]

        i = 0
        noyaux = 0
        while i < len(p):
            if p[i] not in voyelles:
                i += 1
                continue
            trouve = None
            for groupe in sorted(groupes_voyelles, key=len, reverse=True):
                if p.startswith(groupe, i):
                    trouve = groupe
                    break
            if trouve:
                noyaux += 1
                i += len(trouve)
            else:
                noyaux += 1
                i += 1
            # Consommer les voyelles adjacentes qui font partie du même noyau,
            # par exemple dans « eau » ou « oi ».
            while i < len(p) and p[i] in voyelles:
                adjacent = next(
                    (g for g in sorted(groupes_voyelles, key=len, reverse=True)
                     if p.startswith(g, i)),
                    None
                )
                if adjacent:
                    i += len(adjacent)
                else:
                    break
        total += max(1, noyaux)

    return max(1, total)

def parse_word_to_blocks(word, sounds_dict=None, is_plural_verb=False, keep_final_consonant=False, is_end_of_sentence=False):
    blocks = []
    clean_word = word.strip(".,;:?!'\\«» ")
    w_lower = clean_word.lower()
    n = len(word)
    i = 0
    vowels_set = "aeiouyàâäéèêëîïôöùûüÿœæ"
    
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
            
        # Sons de secours uniquement lorsque le son n'existe pas dans le code
        # couleur de référence. Le dictionnaire EXACT_COMPLEX_SOUNDS est prioritaire.
        sons_secours = {
            'ch': ('#2980B9', 'ch'),
            'ui': ('#2980B9', 'ui'),
        }
        special_sounds = {son: regle for son, regle in sons_secours.items() if son not in sounds_dict}

        # Chercher d'abord les sons de secours les plus longs, puis utiliser
        # le dictionnaire de référence pour tous les sons qu'il contient.
        matched_special = False
        for length in [4, 3, 2]:
            if i + length <= n:
                sub = w_lower[i:i+length]
                if sub in special_sounds:
                    color, phoneme = special_sounds[sub]
                    blocks.append({'text': word[i:i+length], 'is_muted': False, 'render_type': 'color_text', 'color': color, 'phoneme': phoneme})
                    i += length
                    matched_special = True
                    break
        if matched_special:
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
            is_prev_vowel = (i > 0 and word[i-1].lower() in vowels_set)
            is_next_vowel = (i + 1 < n and word[i+1].lower() in vowels_set)
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
    clean_word_lower = word.lower().strip(".,;:?!'\\«» ")
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
            clean_w = word.lower().strip(".,;:?!'\\«»' ")
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
    st.write("### 🎛️ Options d’adaptation DYS (Cumulables)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Aides aux sons & syllabes :**")
        show_colors = st.checkbox("Colorer selon votre code couleur de référence", value=True, key=f"{key_prefix}_colors")
        show_arcs = st.checkbox("Afficher les ponts syllabiques", value=True, key=f"{key_prefix}_arcs")
        show_phonemes = st.checkbox("Écrire les sons/phonèmes en dessous", value=True, key=f"{key_prefix}_phonemes")
        st.markdown(
            "**Rappel de ton code couleur des sons**"
            "<div style='display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 10px 0;'>"
            "<span style='background:#FF0000;color:#FFFFFF;padding:5px 9px;border-radius:6px;font-weight:700;'>ou — rouge</span>"
            "<span style='background:#6E2C00;color:#FFFFFF;padding:5px 9px;border-radius:6px;font-weight:700;'>on — marron</span>"
            "<span style='background:#E67E22;color:#FFFFFF;padding:5px 9px;border-radius:6px;font-weight:700;'>an — orange</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.write("**Aides à la ligne & visuel :**")
        word_alt = st.checkbox("Alternance des mots (Bleu/Rouge)", value=False, key=f"{key_prefix}_walt")
        line_alt = st.checkbox("Alternance des lignes", value=False, key=f"{key_prefix}_lalt")
        soft_bg = st.checkbox("Surlignage doux du fond", value=False, key=f"{key_prefix}_bg")
    with c3:
        st.write("**Typographie & Police DYS :**")
        font_choice = st.selectbox(
            "Police d’écriture :",
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
        return "\n".join([f"{k} : {format_to_str(v)}" for k, v in content.items()])
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
    "nom": {"label": "Nom", "emoji": "⭐", "couleur": "#f39c12"},
    "verbe": {"label": "Verbe", "emoji": "🟩", "couleur": "#2ecc71"},
    "adjectif": {"label": "Adjectif", "emoji": "🔵", "couleur": "#3498db"},
    "invariable": {"label": "Mot invariable", "emoji": "⬛", "couleur": "#7f8c8d"}
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
    """
    return html_content
def afficher_page_grammaire(fonction_appel_ia):
    st.header("📐 Module Grammaire Visuelle & Accords")

    # Mémo toujours visible sur la page Grammaire
    st.subheader("🎨 Code couleur et règles des accords")
    st.markdown(
        """
        **Code couleur des natures de mots**

        <span style="background-color:#e74c3c;color:white;padding:4px 8px;border-radius:5px;">🔺 Déterminant</span> &nbsp;
        <span style="background-color:#9b59b6;color:white;padding:4px 8px;border-radius:5px;">💖 Pronom</span> &nbsp;
        <span style="background-color:#f39c12;color:#222;padding:4px 8px;border-radius:5px;">⭐ Nom</span> &nbsp;
        <span style="background-color:#2ecc71;color:#102010;padding:4px 8px;border-radius:5px;">🟩 Verbe</span> &nbsp;
        <span style="background-color:#3498db;color:white;padding:4px 8px;border-radius:5px;">🔵 Adjectif</span> &nbsp;
        <span style="background-color:#7f8c8d;color:white;padding:4px 8px;border-radius:5px;">⬛ Mot invariable</span>

        **Règles d’accord avec les couleurs associées**

        <div style="border-left:6px solid #e74c3c;padding:8px 12px;margin:8px 0;background:#fff5f5;">
        <span style="background:#e74c3c;color:white;padding:3px 6px;border-radius:4px;">🔺 DÉTERMINANT</span>
        + <span style="background:#f39c12;color:#222;padding:3px 6px;border-radius:4px;">⭐ NOM</span><br/>
        Le déterminant accompagne le nom. Ils s’accordent en <b>genre</b> et en <b>nombre</b>.
        Exemple : <i>le chat / les chats</i> ; <i>une chatte</i>.
        </div>

        <div style="border-left:6px solid #3498db;padding:8px 12px;margin:8px 0;background:#f2f8ff;">
        <span style="background:#3498db;color:white;padding:3px 6px;border-radius:4px;">🔵 ADJECTIF</span>
        + <span style="background:#f39c12;color:#222;padding:3px 6px;border-radius:4px;">⭐ NOM</span><br/>
        L’adjectif s’accorde avec le nom qu’il précise, en <b>genre</b> et en <b>nombre</b>.
        Exemple : <i>un petit chien / une petite chienne / des petites chiennes</i>.
        </div>

        <div style="border-left:6px solid #2ecc71;padding:8px 12px;margin:8px 0;background:#f2fff5;">
        <span style="background:#9b59b6;color:white;padding:3px 6px;border-radius:4px;">💖 PRONOM</span>
        ou <span style="background:#f39c12;color:#222;padding:3px 6px;border-radius:4px;">⭐ GROUPE NOMINAL</span>
        = <b>SUJET</b> → <span style="background:#2ecc71;color:#102010;padding:3px 6px;border-radius:4px;">🟩 VERBE</span><br/>
        Le verbe s’accorde avec son sujet. Pour trouver le sujet, demande :
        <b>« Qui est-ce qui… ? »</b> ou <b>« Qu’est-ce qui… ? »</b>.
        Exemple : <i>Le garçon joue / Les garçons jouent</i> ; <i>Elle chante / Elles chantent</i>.
        </div>

        **Méthode en 4 étapes :** 1. Je repère le nom ou le sujet. 2. Je cherche les mots qui vont avec.
        3. Je vérifie le genre, le nombre ou la personne. 4. Je relis les terminaisons.

        *Astuce : les symboles accompagnent les couleurs pour que le mémo reste utile même en impression noir et blanc.*
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        label="📥 Télécharger le code couleur et les règles d’accords (PDF imprimable)",
        data=telecharger_pdf_code_couleur(),
        file_name="code_couleur_et_regles_accords.pdf",
        mime="application/pdf",
        key="download_code_couleur_pdf",
    )
    st.divider()
    
    mode_choix = st.radio(
        "Source de la phrase :",
        ["Piocher dans la banque de 100 phrases", "Écrire ma propre phrase", "Générer une phrase inédite avec l'IA"],
        horizontal=True,
        key="mode_grammaire_radio"
    )
    
    historique = charger_historique()
    
    if mode_choix == "Piocher dans la banque de 100 phrases":
        phrase_choisie = st.selectbox(
            "Choisissez une phrase dans la banque :",
            historique,
            format_func=lambda x: x.get("texte", ""),
            key="select_phrase_banque"
        )
        if phrase_choisie:
            st.session_state.phrase_grammaire = phrase_choisie
            
    elif mode_choix == "Écrire ma propre phrase":
        texte_libre = st.text_input("Écrivez votre phrase ici :", key="input_phrase_libre")
        if st.button("Valider et analyser ma phrase", key="btn_valider_libre"):
            if texte_libre.strip():
                with st.spinner("Analyse de votre phrase..."):
                    nouvelle = generer_ou_analyser_phrase_ia(fonction_appel_ia, texte_force=texte_libre)
                if nouvelle:
                    sauvegarder_phrase_dans_historique(nouvelle)
                    st.session_state.phrase_grammaire = nouvelle
                    st.success("Phrase enregistrée et analysée !")
                    st.rerun()
                    
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
    
    tab_ex, tab_exo, tab_acc = st.tabs(["📖 Analyse", "✏️ Symboles", "✍️ Accords"])
    
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
                type_mot = m.get("type", "")
                infos_symbole = SYMBOLES_GRAMMAIRE.get(type_mot, {})
                label_attendu = infos_symbole.get("label", "")
                
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
if menu_selection == "🏠 Présentation":
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
                
                if pytesseract is None:
                    st.error("Le module OCR n'est pas installé. Installe pytesseract et le moteur Tesseract pour activer l'extraction depuis une image. Tu peux utiliser Mes textes personnalisés sans cette option.")
                    extracted_text = ""
                else:
                    extracted_text = pytesseract.image_to_string(img, lang='fra')
                if extracted_text.strip():
                    st.success("Texte extrait avec succès !")
                    opts = build_controls("ocr_ctrl")
                    render_full_dys_text(extracted_text, **opts)
                else:
                    st.warning("Aucun texte n'a pu être extrait de cette image.")
            except Exception as e:
                st.error(f"Erreur OCR : {e}")

elif menu_selection == "✨ Générateur d’histoires":
    st.title("✨ Générateur d’histoires personnalisées")
    st.caption(f"Profil actif : {eleve_actif} · Niveau du profil : {niveau_actif}")
    st.write("Choisis le thème, les centres d’intérêt et les sons à travailler. L’histoire générée reste une proposition à vérifier par l’adulte avant d’être ajoutée à la bibliothèque.")
    c1, c2 = st.columns(2)
    with c1:
        theme = st.text_input("Envie ou thème de l’histoire", placeholder="Ex. : un dragon qui joue au football", key="histoire_gen_theme")
        niveau_options = ["CP", "CE1", "CE2", "CM1", "CM2"]
        niveau_defaut = niveau_actif if niveau_actif in niveau_options else "CE1"
        niveau_index = niveau_options.index(niveau_defaut)
        niveau_histoire = st.selectbox("Niveau de lecture", niveau_options, index=niveau_index, key="histoire_gen_niveau")
    with c2:
        interets_histoire = st.text_input("Centres d’intérêt de l’enfant", placeholder="Ex. : dinosaures, chevaux, espace", key="histoire_gen_interets")
        sons_histoire = st.text_input("Sons ou graphèmes à travailler", placeholder="Ex. : ou, on, ch, oi", key="histoire_gen_sons")
    longueur_histoire = st.selectbox("Longueur", ["Très courte (80 à 120 mots)", "Courte (150 à 200 mots)", "Plus longue (250 à 350 mots)"], index=1, key="histoire_gen_longueur")
    if st.button("🪄 Générer une histoire personnalisée", key="histoire_gen_bouton", type="primary"):
        if not theme.strip():
            st.warning("Indique d’abord le thème ou l’envie de l’enfant.")
        else:
            nombre_mots = {"Très courte (80 à 120 mots)": "80 à 120", "Courte (150 à 200 mots)": "150 à 200", "Plus longue (250 à 350 mots)": "250 à 350"}[longueur_histoire]
            prompt = (
                "Tu es un auteur jeunesse et tu aides un enfant qui apprend à lire en français. "
                f"Écris une histoire originale de {nombre_mots} mots environ, adaptée au niveau {niveau_histoire}. "
                f"Thème demandé : {theme.strip()}. Centres d’intérêt : {interets_histoire.strip() or 'aucun précisé'}. "
                f"Graphèmes/sons à intégrer naturellement : {sons_histoire.strip() or 'aucun imposé'}. "
                "Utilise des phrases claires, un vocabulaire adapté, une intrigue positive et une fin compréhensible. "
                "Évite de prétendre qu’un graphème se prononce toujours de la même façon. "
                "Réponds uniquement avec le titre sur la première ligne, puis le texte de l’histoire."
            )
            try:
                with st.spinner("L’histoire est en cours de création…"):
                    resultat_ia = interroger_ia(prompt, temperature=0.75)
                if not resultat_ia or resultat_ia.startswith("Erreur IA"):
                    st.error("La génération n’a pas abouti. Vérifie la configuration de la clé IA (GROQ_API_KEY ou GEMINI_API_KEY) et les dépendances, puis réessaie.")
                    if resultat_ia:
                        with st.expander("Détail technique pour l’adulte"):
                            st.code(resultat_ia)
                else:
                    lignes_histoire = [ligne.strip() for ligne in resultat_ia.splitlines() if ligne.strip()]
                    titre_histoire = lignes_histoire[0].lstrip("# ").strip()[:100] if lignes_histoire else theme.strip()
                    texte_histoire = "\n".join(lignes_histoire[1:]).strip() if len(lignes_histoire) > 1 else resultat_ia.strip()
                    if not texte_histoire:
                        texte_histoire = resultat_ia.strip()
                    st.session_state["histoire_generee"] = texte_histoire
                    st.session_state["histoire_generee_titre"] = titre_histoire or theme.strip()
                    st.session_state["histoire_generee_niveau"] = niveau_histoire
                    st.session_state["histoire_generee_sons"] = sons_histoire.strip()
                    st.session_state["histoire_generee_interets"] = interets_histoire.strip()
                    st.success("Histoire générée. Relis-la avant de la proposer à l’enfant.")
            except Exception as exc:
                st.error("Une erreur inattendue a interrompu la génération. La page reste disponible : vérifie la configuration IA puis réessaie.")
                with st.expander("Détail technique pour l’adulte"):
                    st.code(f"{type(exc).__name__}: {exc}")
    if st.session_state.get("histoire_generee"):
        st.divider()
        st.subheader(st.session_state.get("histoire_generee_titre", "Histoire générée"))
        opts = build_controls("histoire_gen")
        try:
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
        except Exception as exc:
            st.warning("L’affichage adapté a rencontré un problème ; le texte brut reste disponible ci-dessous.")
            st.text_area("Texte de l’histoire", value=st.session_state["histoire_generee"], height=240, key="histoire_gen_brut_secours")
            with st.expander("Détail technique pour l’adulte"):
                st.code(f"{type(exc).__name__}: {exc}")
        if st.button("📚 Enregistrer comme proposition à valider par l’adulte", key="histoire_gen_enregistrer"):
            titre_sauve = st.session_state.get("histoire_generee_titre", "Histoire personnalisée")
            proposer_histoire(
                eleve_actif, titre_sauve, st.session_state["histoire_generee"],
                "Générée par IA", st.session_state.get("histoire_generee_niveau", niveau_actif),
                st.session_state.get("histoire_generee_sons", ""),
                st.session_state.get("histoire_generee_interets", ""), "a_valider"
            )
            st.success("Proposition enregistrée. L’adulte pourra la relire et l’approuver dans « Bibliothèque d’histoires ».")
            st.rerun()

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


elif menu_selection == "🎯 Entraînement interactif":
    afficher_entrainement(eleve_actif, niveau_actif)

elif menu_selection == "📊 Mes progrès":
    afficher_progres(eleve_actif)

elif menu_selection == "⚙️ Profil & sauvegarde":
    st.title("⚙️ Profil et sauvegarde des données")
    st.write("Le prénom/pseudonyme, le niveau et les résultats sont enregistrés dans une base SQLite sur la machine qui exécute l’application. Si l’application est hébergée en ligne, cette machine est le serveur d’hébergement.")
    st.markdown("### Exporter mes résultats")
    resultats_export = lire_resultats(eleve_actif)
    if resultats_export:
        st.download_button("📥 Télécharger mes résultats (JSON)", data=json.dumps(resultats_export, ensure_ascii=False, indent=2), file_name=f"resultats_{re.sub(r'[^a-zA-Z0-9_-]', '_', eleve_actif)}.json", mime="application/json")
        csv_lignes = ["date,niveau,notion,question,reponse,bonne_reponse,correct"]
        import csv as _csv
        import io as _io
        buffer_csv = _io.StringIO()
        writer = _csv.DictWriter(buffer_csv, fieldnames=["date_utc", "niveau", "notion", "question", "reponse", "bonne_reponse", "correct"])
        writer.writeheader()
        for r in resultats_export:
            writer.writerow({k:r.get(k, "") for k in writer.fieldnames})
        st.download_button("📊 Télécharger mes résultats (CSV)", data=buffer_csv.getvalue(), file_name=f"resultats_{re.sub(r'[^a-zA-Z0-9_-]', '_', eleve_actif)}.csv", mime="text/csv")
    else:
        st.caption("Les téléchargements seront disponibles après les premiers exercices.")
    st.markdown("### Données et confidentialité")
    st.markdown("""- Les résultats sont stockés localement dans SQLite, pas dans un compte en ligne.
- Si l’application est déployée sur un hébergeur éphémère, le fichier peut être perdu au redémarrage : configure un volume persistant.
- Les fonctions IA existantes peuvent transmettre les textes saisis au fournisseur IA configuré. Évite d’y saisir des informations personnelles sensibles.""")
    st.markdown("### Réinitialiser les résultats de ce profil")
    confirmation = st.checkbox(f"Je confirme vouloir supprimer les résultats de « {eleve_actif} ».", key="confirmer_suppression_resultats")
    if st.button("🗑️ Supprimer les résultats de ce profil", disabled=not confirmation, type="secondary"):
        with connexion_db() as conn:
            conn.execute("DELETE FROM resultats WHERE eleve=?", (eleve_actif,))
        st.session_state.pop("confirmer_suppression_resultats", None)
        st.success("Les résultats de ce profil ont été supprimés.")
        st.rerun()


# Extensions supplémentaires : ces pages sont ajoutées au menu sans remplacer les modules existants.
if menu_selection == "📚 Bibliothèque d’histoires":
    afficher_bibliotheque_histoires(eleve_actif, niveau_actif)
elif menu_selection == "📝 Mes textes personnalisés":
    afficher_textes_personnalises(eleve_actif, niveau_actif)
elif menu_selection == "🎤 Atelier de dictée complet":
    afficher_atelier_dictee(eleve_actif, niveau_actif)
elif menu_selection == "🎨 Réglages DYS et code couleur":
    afficher_reglages_dys()
