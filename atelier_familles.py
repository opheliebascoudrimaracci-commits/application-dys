"""Module complémentaire : adaptations parentales et PDF imprimables.
Les analyses automatiques sont indicatives : correction adulte avant impression.
"""
import re, io, html, json, sqlite3
from pathlib import Path
from xml.sax.saxutils import escape as xesc
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib import colors
from reportlab.lib.units import mm

EXCEPTIONS = {
 'école':'é-cole', 'minute':'mi-nu-te', 'maminounou':'ma-mi-nou-nou',
 'brun':'brun', 'lapin':'la-pin', 'sapin':'sa-pin', 'vin':'vin',
 'banane':'ba-na-ne', 'table':'ta-ble', 'bonjour':'bon-jour',
 'maison':'mai-son', 'voiture':'voi-ture', 'chapeau':'cha-peau',
}
SONS = [('eau','#bc8800','o'),('ain','#16804b','in'),('ein','#16804b','in'),
 ('œu','#187a9e','eu'),('ou','#d92323','ou'),('on','#784212','on'),
 ('un','#1667ba','1'),('an','#bd6300','an'),('en','#bd6300','an'),
 ('in','#16804b','in'),('au','#bc8800','o'),('ai','#7738a1','è'),
 ('ei','#7738a1','è'),('ch','#aa5c22','ch'),('oi','#925f13','wa'),
 ('eu','#187a9e','eu'),('é','#7d3c98','é'),('qu','#6741a5','k')]
VOWELS='aeiouyàâäéèêëïîôöùûüÿœ'
WORD=re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿŒœ]+)*")

def init_db(db):
 with sqlite3.connect(db) as c:
  c.execute('CREATE TABLE IF NOT EXISTS adaptations_mots (profil TEXT, mot TEXT, decoupe TEXT, PRIMARY KEY(profil,mot))')
  c.execute('CREATE TABLE IF NOT EXISTS mots_reperes (profil TEXT, mot TEXT, PRIMARY KEY(profil,mot))')

def lire_decoupes(db,profil):
 with sqlite3.connect(db) as c:
  return {a:b for a,b in c.execute('SELECT mot,decoupe FROM adaptations_mots WHERE profil=?',(profil,))}

def valide_decoupe(mot, decoupe):
 parties=[x.strip() for x in decoupe.split('-')]
 return bool(parties) and all(parties) and ''.join(parties).casefold()==mot.casefold()

def decouper(mot, corrections):
 low=mot.lower()
 if low in corrections and valide_decoupe(mot,corrections[low]):return corrections[low].split('-')
 if low in EXCEPTIONS:return EXCEPTIONS[low].split('-')
 # Approximation prudente : n'est pas présentée comme une analyse fiable.
 # Sépare avant une consonne unique entre deux noyaux vocaliques.
 clusters=re.findall(r'eau|ain|ein|œu|ou|oi|au|ai|ei|eu|[aeiouyàâäéèêëïîôöùûüÿœ]|[^aeiouyàâäéèêëïîôöùûüÿœ]+',low)
 starts=[]; pos=0
 for cl in clusters:
  if any(ch in VOWELS for ch in cl):starts.append(pos)
  pos+=len(cl)
 if len(starts)<=1:return [mot]
 boundaries=[]
 for a,b in zip(starts,starts[1:]):
  between=low[a+1:b]
  cut=b-1 if len(between)==1 else (b-2 if len(between)>1 else b)
  if 0<cut<len(mot) and (not boundaries or cut>boundaries[-1]):boundaries.append(cut)
 result=[]; p=0
 for cut in boundaries:result.append(mot[p:cut]);p=cut
 result.append(mot[p:])
 return result if all(result) else [mot]

def sons_segments(syllable, fullword, offset):
 out=[];i=0;lower=fullword.lower()
 while i<len(syllable):
  found=None
  for sound,color,hint in SONS:
   if syllable[i:].lower().startswith(sound):
    at=offset+i; end=at+len(sound)
    # Les graphèmes nasaux sont bloqués devant une voyelle, ou n/m doublé.
    if sound in ('in','un','an','en','on','ain','ein'):
     if end<len(fullword) and (lower[end] in VOWELS+'nm'):continue
     if sound=='in' and lower in ('minute','maminounou'):continue
    # éviter de colorer la terminaison verbale muette -ent
    if sound=='en' and lower.endswith('ent') and end==len(fullword)-1:continue
    found=(sound,color,hint);break
  if found:
   s,color,hint=found;out.append((syllable[i:i+len(s)],color,hint));i+=len(s)
  else:
   # s entre deux voyelles = z (cas général, exceptions possibles)
   at=offset+i; ch=syllable[i]
   if ch.lower()=='s' and 0<at<len(fullword)-1 and lower[at-1] in VOWELS and lower[at+1] in VOWELS:
    out.append((ch,'#0d9488','z'))
   elif ch.lower()=='c' and at+1<len(fullword) and lower[at+1] in 'eéèêiy':out.append((ch,'#925f13','s'))
   elif ch.lower()=='g' and at+1<len(fullword) and lower[at+1] in 'eéèêiy':out.append((ch,'#925f13','j'))
   else:out.append((ch,None,None))
   i+=1
 return out

def word_markup(word,settings,corrections):
 syllables=decouper(word,corrections)
 result=[];offset=0
 for syll in syllables:
  segs=sons_segments(syll,word,offset);offset+=len(syll)
  spans=[]
  for chars,color,hint in segs:
   for j,ch in enumerate(chars):
    symbol={'b':'bec','d':'dos','p':'pattes','q':'queue','v':'vague','f':'fusée'}.get(ch.lower()) if settings['reperes'] else None
    style=f'color:{color};font-weight:700;' if color and settings['couleurs'] else 'color:#161616;'
    ph=hint if hint and (settings['phon'] in ('complexes','complet')) and j==0 else ''
    if settings['phon']=='complet' and not ph:ph=ch
    hint_html=f'<small class="hint">{html.escape(ph)}</small>' if ph else '<small class="hint">&nbsp;</small>'
    mark=f'<small class="repere">{html.escape(symbol)}</small>' if symbol else ''
    spans.append(f'<span class="lettre"><span style="{style}">{html.escape(ch)}</span>{hint_html}{mark}</span>')
  arc='<span class="arc"></span>' if settings['arcs'] else ''
  result.append(f'<span class="syll">{"".join(spans)}{arc}</span>')
 return ''.join(result)

def html_lecture(texte,settings,corrections):
 chunks=[];last=0
 for m in WORD.finditer(texte):
  chunks.append(html.escape(texte[last:m.start()]).replace('\n','<br>'))
  chunks.append(f'<span class="mot">{word_markup(m.group(),settings,corrections)}</span>')
  last=m.end()
 chunks.append(html.escape(texte[last:]).replace('\n','<br>'))
 return ''.join(chunks)

CSS='''<style>.feuille{background:white;color:#161616;padding:22px;border:1px solid #ddd;line-height:2.6;letter-spacing:.02em;font-family:Arial,sans-serif;overflow-wrap:break-word}.mot{display:inline-block;white-space:nowrap;margin:0 .13em}.syll{display:inline-flex;position:relative;white-space:nowrap;padding-bottom:.23em;margin-right:1px}.arc{position:absolute;bottom:.06em;left:2%;width:96%;height:.22em;border:2px solid #4788c8;border-top:0;border-radius:0 0 50% 50%;box-sizing:border-box}.lettre{display:inline-flex;flex-direction:column;align-items:center;vertical-align:top;line-height:1.1}.hint{font-size:.42em;line-height:1.2;min-height:1.2em;color:#444}.repere{font-size:.36em;color:#555;line-height:1.1}</style>'''

def pdf_texte(titre,texte,settings,corrections,format_papier='A4',lignes=False):
 """PDF vectoriel : arcs suivent les largeurs réelles des syllabes."""
 from reportlab.pdfbase.ttfonts import TTFont
 from reportlab.pdfbase import pdfmetrics
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 font='Helvetica'
 if Path(fontpath).exists():
  if 'DejaVuMathis' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('DejaVuMathis',fontpath))
  font='DejaVuMathis'
 page=A4 if format_papier=='A4' else A5
 buffer=io.BytesIO(); from reportlab.pdfgen import canvas
 c=canvas.Canvas(buffer,pagesize=page);W,H=page;left=18*mm;right=W-18*mm;y=H-22*mm
 def newpage():
  nonlocal y
  c.showPage();y=H-22*mm
 c.setFont(font,16);c.drawString(left,y,titre[:65]);y-=15*mm
 fs=settings['taille'];lh=fs*settings['interligne'];x=left
 for token in re.findall(r"\n|\s+|[^\s]+",texte):
  if token=='\n':x=left;y-=lh;continue
  if token.isspace():x+=pdfmetrics.stringWidth(' ',font,fs)*len(token);continue
  width=pdfmetrics.stringWidth(token,font,fs)
  if x+width>right and x>left:x=left;y-=lh
  if y<22*mm:newpage()
  for match in WORD.finditer(token):
   # ponctuation et segments de mot sont conservés dans leur ordre
   pass
  pos=0
  for match in WORD.finditer(token):
   before=token[pos:match.start()];c.setFont(font,fs);c.setFillColor(colors.black);c.drawString(x,y,before);x+=pdfmetrics.stringWidth(before,font,fs)
   word=match.group();offset=0
   for syll in decouper(word,corrections):
    sx=x
    for chars,col,hint in sons_segments(syll,word,offset):
     for j,ch in enumerate(chars):
      c.setFillColor(colors.HexColor(col) if col and settings['couleurs'] else colors.black)
      c.setFont(font,fs);c.drawString(x,y,ch)
      cw=pdfmetrics.stringWidth(ch,font,fs)
      if settings['phon']!='aucune' and ((hint and j==0) or settings['phon']=='complet'):
       ph=hint if hint and j==0 else ch
       c.setFillColor(colors.grey);c.setFont(font,max(7,fs*.38));c.drawCentredString(x+cw/2,y-8,ph)
      if settings['reperes'] and ch.lower() in 'bdpqvf':
       rep={'b':'bec','d':'dos','p':'pattes','q':'queue','v':'vague','f':'fusée'}[ch.lower()]
       c.setFont(font,max(6,fs*.30));c.setFillColor(colors.grey);c.drawCentredString(x+cw/2,y-15,rep)
      x+=cw
    if settings['arcs']:
     c.setStrokeColor(colors.HexColor('#4788c8'));c.setLineWidth(1.1)
     c.bezier(sx,y-5,sx+(x-sx)*.25,y-12,sx+(x-sx)*.75,y-12,x,y-5)
    offset+=len(syll)
   pos=match.end()
  after=token[pos:];c.setFillColor(colors.black);c.setFont(font,fs);c.drawString(x,y,after);x+=pdfmetrics.stringWidth(after,font,fs)
 if lignes:
  y-=lh
  while y>22*mm:
   c.setStrokeColor(colors.lightgrey);c.line(left,y,right,y);y-=12*mm
 c.save();return buffer.getvalue()

def pdf_memo(mot,phrase):
 buf=io.BytesIO();from reportlab.pdfgen import canvas
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 font='Helvetica';path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 if Path(path).exists():
  if 'DejaVuMathis' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('DejaVuMathis',path))
  font='DejaVuMathis'
 c=canvas.Canvas(buf,pagesize=A4);w,h=A4
 c.setFont(font,17);c.drawString(20*mm,h-25*mm,'Je mémorise mon mot')
 c.setFont(font,32);c.drawString(20*mm,h-52*mm,mot[:28])
 c.setFont(font,12)
 from reportlab.lib.utils import simpleSplit
 for i,line in enumerate(simpleSplit(phrase,font,12,w-40*mm)):c.drawString(20*mm,h-75*mm-i*7*mm,line)
 c.setFont(font,12);c.drawString(20*mm,h-108*mm,'Mon dessin :')
 c.setStrokeColor(colors.lightgrey);c.rect(20*mm,25*mm,w-40*mm,h-145*mm)
 c.save();return buf.getvalue()

def page(profil,db,ia=None):
 init_db(db)
 st.title('🖨️ Adapter et imprimer les devoirs')
 st.caption('Les parents préparent les supports. Aucun exercice supplémentaire n’est imposé.')
 titre=st.text_input('Titre du document',value='Mes devoirs adaptés',key='fam_titre')
 texte=st.text_area('Collez le texte de l’école ou d’un livre',height=180,key='fam_texte')
 c1,c2,c3=st.columns(3)
 with c1:couleurs=st.checkbox('Couleurs des sons',True,key='fam_couleurs');arcs=st.checkbox('Arcs syllabiques',True,key='fam_arcs')
 with c2:phon=st.selectbox('Phonétique texto',['complexes','aucune','complet'],key='fam_phon');reperes=st.checkbox('Repères b d p q v f',False,key='fam_reperes')
 with c3:taille=st.slider('Taille du texte',16,32,23,key='fam_taille');interligne=st.slider('Interligne',1.6,3.5,2.4,.1,key='fam_ligne')
 settings=dict(couleurs=couleurs,arcs=arcs,phon=phon,reperes=reperes,taille=taille,interligne=interligne)
 corrections=lire_decoupes(db,profil)
 with st.expander('✏️ Vérifier ou corriger les syllabes',expanded=False):
  mot=st.text_input('Mot à corriger',key='fam_mot').strip()
  if mot:
   st.caption('Proposition : '+' – '.join(decouper(mot,corrections)))
   proposition=st.text_input('Découpage avec des tirets',value='-'.join(decouper(mot,corrections)),key='fam_decoupe')
   if st.button('Enregistrer ce découpage'):
    if valide_decoupe(mot,proposition):
     with sqlite3.connect(db) as c:c.execute('INSERT OR REPLACE INTO adaptations_mots VALUES(?,?,?)',(profil,mot.lower(),proposition))
     st.success('Correction conservée pour ce profil.');st.rerun()
    else:st.error('Les lettres doivent rester exactement celles du mot, dans le même ordre.')
  st.caption('Vérifiez les mots inconnus : le découpage automatique est approximatif.')
 if texte.strip():
  st.markdown(CSS,unsafe_allow_html=True)
  st.markdown(f'<div class="feuille" style="font-size:{taille}px">{html_lecture(texte,settings,corrections)}</div>',unsafe_allow_html=True)
  st.caption('Les repères b/d/p/q sont provisoirement nommés : il manque le dessin original de l’oiseau pour découper les vraies pièces.')
  format_papier=st.radio('Papier',['A4','A5'],horizontal=True,key='fam_papier')
  lignes=st.checkbox('Ajouter des lignes pour écrire',False,key='fam_lignes')
  st.download_button('📄 Télécharger le PDF adapté',pdf_texte(titre,texte,settings,corrections,format_papier,lignes),file_name='devoirs_adaptes.pdf',mime='application/pdf')
  clean={**settings,'couleurs':False,'arcs':False,'phon':'aucune','reperes':False}
  st.download_button('📄 Télécharger la version sans aides',pdf_texte(titre,texte,clean,corrections,format_papier,lignes),file_name='devoirs_sans_aides.pdf',mime='application/pdf')
  with st.expander('⭐ Conserver un mot difficile'):
   mots=sorted(set(m.group().lower() for m in WORD.finditer(texte)))
   choix=st.selectbox('Mot',mots,key='fam_choix')
   if st.button('Ajouter au carnet des parents'):
    with sqlite3.connect(db) as c:c.execute('INSERT OR IGNORE INTO mots_reperes VALUES(?,?)',(profil,choix))
    st.success('Mot conservé.')
 st.divider();st.subheader('✏️ Je mémorise mon mot')
 with sqlite3.connect(db) as c: mots=[r[0] for r in c.execute('SELECT mot FROM mots_reperes WHERE profil=? ORDER BY mot',(profil,))]
 if mots:st.caption('Mots conservés : '+', '.join(mots[:40]))
 mot_memo=st.text_input('Mot à mémoriser',key='fam_memo_mot')
 difficile=st.text_input('Lettres difficiles (ex. rr)',key='fam_memo_diff')
 if st.button('Proposer une phrase mnémotechnique') and mot_memo.strip():
  if ia:
   reponse=ia(f'Propose UNE phrase mnémotechnique courte et imagée pour retenir l’orthographe exacte du mot français « {mot_memo} », particulièrement « {difficile} ». Pas d’exercice, pas de conseil, une phrase seulement.',temperature=.5)
   if not reponse.startswith('Erreur IA'):st.session_state['fam_phrase']=reponse
   else:st.warning('IA indisponible : écrivez votre phrase vous-même.')
  else:st.info('Écrivez votre phrase personnalisée.')
 phrase=st.text_area('Phrase mnémotechnique modifiable',key='fam_phrase')
 if mot_memo.strip() and phrase.strip():st.download_button('🖨️ Imprimer la fiche avec espace pour dessiner',pdf_memo(mot_memo,phrase),file_name='mon_mot_a_memoriser.pdf',mime='application/pdf')
