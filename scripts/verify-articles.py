#!/usr/bin/env python3
"""Vérifie qu'un fragment d'article respecte les conventions du blog.
Usage : python3 scripts/verify-articles.py _content/articles-*.html"""
import re, sys, glob, json, os

SEUILS = {'mots_min': 1800, 'mots_max': 2600, 'h2_min': 9, 'h2_max': 16,
          'faq_min': 5, 'faq_max': 8, 'lead_min': 25, 'lead_max': 60}

# mots_min : 1 800 depuis le lot 7. Certains sujets techniques ne portent pas
# 2 200 mots (llms.txt, contenu dupliqué) ; 1 800 mots denses valent mieux que
# 2 300 dilués. La cible de rédaction reste 2 200-2 400 pour la majorité.

# Marqueurs IA et formulations interdites (conformité Google Ads)
INTERDITS = [
    r'\bgarantis?\b', r'\bsans blabla', r'\bsans jargon', r'\bà l\'aveugle\b',
    r'\ble meilleur\b', r'\bn°1\b', r'\bnuméro 1\b', r'\brévolutionnaire\b',
    r'\bincroyable\b', r'\bmagique\b', r'\bgame changer\b', r'\bdisruptif\b',
    r'[🚀🔍📊✅⭐💡🎯]',           # emoji dans le corps
    r"n'hésitez pas à",              # tic de langage
    r"\bIl est important de noter\b", r"\bDans un monde où\b",
    r"\bforce est de constater\b", r"\bà l'ère du numérique\b",
]

def texte(s):
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S | re.I)
    return ' '.join(re.sub(r'<[^>]+>', ' ', s).split())

def controler(chemin):
    s = open(chemin, encoding='utf-8').read()
    nom = os.path.basename(chemin)
    pb, avert = [], []

    # --- Structure
    if s.count('<h1') != 1: pb.append(f"{s.count('<h1')} H1 (1 attendu)")
    h2 = len(re.findall(r'<h2', s))
    if not (SEUILS['h2_min'] <= h2 <= SEUILS['h2_max']):
        pb.append(f"{h2} H2 (attendu {SEUILS['h2_min']}-{SEUILS['h2_max']})")
    faq = len(re.findall(r'<details', s))
    if not (SEUILS['faq_min'] <= faq <= SEUILS['faq_max']):
        avert.append(f"{faq} FAQ (attendu {SEUILS['faq_min']}-{SEUILS['faq_max']})")

    corps = re.search(r'class="article-body[^"]*">(.*?)(?:</section>|<script)', s, re.S)
    n = len(texte(corps.group(1)).split()) if corps else 0
    if not (SEUILS['mots_min'] <= n <= SEUILS['mots_max']):
        pb.append(f"{n} mots (attendu {SEUILS['mots_min']}-{SEUILS['mots_max']})")

    lead = re.search(r'<p class="lead">(.*?)</p>', s, re.S)
    nl = len(texte(lead.group(1)).split()) if lead else 0
    if not lead: pb.append("pas de chapô .lead")
    elif not (SEUILS['lead_min'] <= nl <= SEUILS['lead_max']):
        avert.append(f"chapô {nl} mots (attendu {SEUILS['lead_min']}-{SEUILS['lead_max']})")

    # --- Schémas obligatoires
    for t in ('Article', 'BreadcrumbList', 'FAQPage'):
        if f'"@type":"{t}"' not in s.replace(' ', ''):
            pb.append(f"schéma {t} absent")
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(b)
        except Exception as e: pb.append(f"JSON-LD invalide : {str(e)[:40]}")

    # --- Conformité et ton
    bas = texte(s).lower()
    SUPERLATIFS = (r'\ble meilleur\b', r'\bn°1\b', r'\bnuméro 1\b')
    A_VERIFIER = (r'\bgarantie?s?\b', r'\bremboursement\b')
    for motif in INTERDITS:
        m = re.search(motif, bas, re.I)
        if not m: continue
        # Un superlatif peut être rhétorique (« le meilleur exemple ? celui-ci »)
        # ou une promesse commerciale. Avertissement, pas échec.
        if motif in SUPERLATIFS:
            avert.append(f"superlatif à vérifier : « {m.group(0)} »")
        elif motif in A_VERIFIER:
            avert.append(f"notion à vérifier : « {m.group(0)} »")
        else:
            pb.append(f"formulation interdite : « {m.group(0)} »")

    # --- Liens : absolus uniquement, et le maillage
    # Un lien relatif ne passe que s'il résout vers un fichier réel. Un « ../ »
    # depuis /articles/<slug>/ remonte à /articles/, qui n'a pas d'index :
    # c'est un 404. Il a été toléré ici parce que les articles en ligne
    # l'utilisaient — la production portait le même défaut, ce n'était pas
    # une preuve de validité.
    slug = nom[len('articles-'):-len('.html')] if nom.startswith('articles-') else ''
    for m in re.findall(r'(?:href|src)="((?!/|http|#|mailto|tel)[^"]+)"', s):
        cible = os.path.normpath(os.path.join('articles', slug, m))
        if not (os.path.isfile(cible) or os.path.isfile(os.path.join(cible, 'index.html'))):
            pb.append(f"lien relatif qui ne résout pas : {m} (→ /{cible.replace(os.sep, '/')}/)")
    for m in re.findall(r'srcset="([^"]*)"', s):
        for c in m.split(','):
            if c.strip() and not c.strip().startswith('/'):
                pb.append(f"srcset relatif : {c.strip()[:40]}")

    # --- CTA et maillage
    # Deux formes de lien WhatsApp coexistent dans les articles en ligne :
    # wa.me et api.whatsapp.com. Les deux sont acceptées.
    # Toute page de service du site vaut CTA : le bon renvoi dépend du sujet
    # de l'article (automatisation, IA, site web, diagnostic).
    SERVICES = ('diagnostic_eperformance.html', 'automatisation.html', 'ia.html',
                '/site-web.html', 'formation.html', 'ebook.html')
    a_cta = ('wa.me' in s or 'api.whatsapp.com' in s
             or any(x in s for x in SERVICES))
    if not a_cta:
        pb.append("aucun CTA (diagnostic, WhatsApp ou page de service)")
    if s.count('href="/') < 4:
        avert.append("maillage interne faible")

    return nom, pb, avert, n, h2, faq

if __name__ == '__main__':
    fichiers = sys.argv[1:] or glob.glob('_content/articles-*.html')
    if not fichiers:
        print("  Aucun fichier à vérifier"); sys.exit(0)
    ko = 0
    print(f"  {'Article':48} {'mots':>5} {'H2':>3} {'FAQ':>4}")
    for f in sorted(fichiers):
        nom, pb, avert, n, h2, faq = controler(f)
        etat = 'ÉCHEC' if pb else ('WARN ' if avert else 'OK   ')
        if pb: ko += 1
        print(f"  {etat} {nom[:44]:44} {n:>5} {h2:>3} {faq:>4}")
        for p in pb: print(f"        ✗ {p}")
        for a in avert: print(f"        ! {a}")
    print(f"\n  {len(fichiers)-ko}/{len(fichiers)} article(s) conforme(s)")
    sys.exit(1 if ko else 0)
