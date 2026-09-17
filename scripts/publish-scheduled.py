#!/usr/bin/env python3
"""Publie les articles du blog dont la date de parution est arrivée.

Le blog ePerformance publie cinq articles par jour. Ce script est appelé par
le workflow GitHub Actions une fois par jour. Il fait passer en ligne tout ce
qui est dû, puis reconstruit le sitemap et l'index en conséquence.

Idempotent : relancé deux fois le même jour, il ne republie rien. Un article
déjà marqué published n'est jamais retouché.

Sortie : 0 si au moins un article a été publié, 1 sinon. Le workflow s'en sert
pour décider s'il doit committer.

Usage :
    python3 scripts/publish-scheduled.py                 # publie ce qui est dû
    python3 scripts/publish-scheduled.py --date 2026-09-25   # simule une date
    python3 scripts/publish-scheduled.py --dry-run       # n'écrit rien
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE = os.path.join(RACINE, "_schedule.json")
SITEMAP = os.path.join(RACINE, "sitemap.xml")
INDEX = os.path.join(RACINE, "_content", "index.html")
BASE = "https://blog.eperformance.pro"

# Pages qui ne sont pas des articles : toujours présentes au sitemap.
PAGES_FIXES = [
    ("", "weekly", "1.0"),
    ("acquisition/", "weekly", "0.9"),
    ("site-web/", "weekly", "0.9"),
    ("seo/", "weekly", "0.9"),
    ("business/", "weekly", "0.9"),
    ("a-propos/", "weekly", "0.7"),
    ("contact/", "weekly", "0.7"),
]


def lire_schedule():
    with open(SCHEDULE, encoding="utf-8") as f:
        return json.load(f)


def ecrire_schedule(sched):
    with open(SCHEDULE, "w", encoding="utf-8") as f:
        json.dump(sched, f, ensure_ascii=False, indent=2)
        f.write("\n")


def articles_dus(sched, aujourdhui):
    """Articles planifiés dont la date est atteinte et non encore publiés."""
    dus = []
    for a in sched["articles"]:
        if a.get("published"):
            continue
        if dt.date.fromisoformat(a["date"]) <= aujourdhui:
            dus.append(a)
    return sorted(dus, key=lambda a: (a["date"], a["heure"]))


def infos_article(slug):
    """Titre, catégorie et accroche d'un fragment, pour l'index du blog."""
    chemin = os.path.join(RACINE, "_content", f"articles-{slug}.html")
    with open(chemin, encoding="utf-8") as f:
        s = f.read()

    def texte(x):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()

    titre = texte(re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1))
    cat = texte(re.search(r'<span class="article-category">(.*?)</span>', s, re.S).group(1))

    accroche = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        d = json.loads(m.group(1))
        if d.get("@type") == "Article":
            accroche = d.get("description", "")
            break
    return titre, cat, accroche


def ecrire_sitemap(sched, aujourdhui, dry_run):
    """Régénère le sitemap : pages fixes + articles publiés, rien d'autre."""
    publies = [a for a in sched["articles"] if a.get("published")]
    publies.sort(key=lambda a: (a["date"], a["heure"]), reverse=True)
    jour = aujourdhui.isoformat()

    blocs = []
    for chemin, freq, prio in PAGES_FIXES:
        blocs.append(
            f"  <url>\n"
            f"    <loc>{BASE}/{chemin}</loc>\n"
            f"    <lastmod>{jour}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            f"  </url>"
        )
    for a in publies:
        blocs.append(
            f"  <url>\n"
            f"    <loc>{BASE}/articles/{a['slug']}/</loc>\n"
            f"    <lastmod>{a['date']}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>"
        )

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n\n'
           + "\n".join(blocs) + "\n</urlset>\n")

    if not dry_run:
        with open(SITEMAP, "w", encoding="utf-8") as f:
            f.write(xml)
    return len(publies)


def ecrire_index(sched, dry_run):
    """Remplit la section ARTICLES-PUBLIES de l'index du blog."""
    publies = [a for a in sched["articles"] if a.get("published")]
    publies.sort(key=lambda a: (a["date"], a["heure"]), reverse=True)

    cartes = []
    for a in publies:
        titre, cat, accroche = infos_article(a["slug"])
        if len(accroche) > 118:
            accroche = accroche[:115].rstrip(" ,;:") + "…"
        cartes.append(
            f'      <a href="/articles/{a["slug"]}/" class="article-card">\n'
            f'        <div class="article-card-body">\n'
            f'          <span class="article-category">{cat}</span>\n'
            f'          <h3>{titre}</h3>\n'
            f'          <p class="small">{accroche}</p>\n'
            f'        </div>\n'
            f'      </a>'
        )

    with open(INDEX, encoding="utf-8") as f:
        s = f.read()
    debut = s.find("<!-- ARTICLES-PUBLIES:DEBUT -->")
    fin = s.find("<!-- ARTICLES-PUBLIES:FIN -->")
    if debut < 0 or fin < 0:
        raise SystemExit("marqueurs ARTICLES-PUBLIES absents de _content/index.html")

    tete = s[:debut]
    queue = s[fin:]
    grille = ('    <div class="articles-grid mt-4">\n' + "\n".join(cartes)
              + ('\n    </div>\n' if cartes else ''))
    # réinjecte la grille dans la section, entre le <p class="lead"> et </div></div>
    corps = s[debut:fin]
    corps = re.sub(r'<div class="articles-grid mt-4">.*?</div>\s*(?=</div>)',
                   grille.rstrip() + "\n    ", corps, flags=re.S)
    nouveau = tete + corps + queue

    if not dry_run:
        with open(INDEX, "w", encoding="utf-8") as f:
            f.write(nouveau)
    return len(publies)


def lancer(commande):
    r = subprocess.run(commande, cwd=RACINE)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Publie les articles dus.")
    ap.add_argument("--date", help="simule une date (AAAA-MM-JJ)")
    ap.add_argument("--dry-run", action="store_true", help="n'écrit rien")
    args = ap.parse_args()

    aujourdhui = (dt.date.fromisoformat(args.date) if args.date
                  else dt.datetime.now(dt.timezone.utc).date())

    sched = lire_schedule()
    dus = articles_dus(sched, aujourdhui)

    total_publies = sum(1 for a in sched["articles"] if a.get("published"))
    print(f"  date du jour    : {aujourdhui.isoformat()}")
    print(f"  déjà en ligne   : {total_publies} article(s)")
    print(f"  à publier       : {len(dus)} article(s)")

    if not dus:
        print("  rien à publier aujourd'hui")
        return 1

    for a in dus:
        print(f"    + #{a['numero']:>2} {a['slug']:36} {a['date']} {a['heure']}")

    if not args.dry_run:
        for a in dus:
            a["published"] = True
        ecrire_schedule(sched)

    n_sitemap = ecrire_sitemap(sched, aujourdhui, args.dry_run)
    n_index = ecrire_index(sched, args.dry_run)
    print(f"  sitemap         : {n_sitemap} article(s) publié(s) listé(s)")

    if args.dry_run:
        print("  simulation : aucune écriture, composition non lancée")
        return 0

    if not lancer([sys.executable, "_build/compose.py"]):
        raise SystemExit("la composition a échoué — rien n'a été publié proprement")

    ok = lancer([sys.executable, "scripts/verify-articles.py"])
    print("  vérification    : " + ("OK" if ok else "ÉCHEC — à corriger avant de committer"))

    print(f"  {len(dus)} article(s) publié(s) · index à {n_index} article(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
