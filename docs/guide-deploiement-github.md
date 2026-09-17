# Guide — déploiement

## Hébergement

GitHub Pages, publication **par branche** depuis `main`. Aucun workflow de build : le HTML est composé localement puis committé.

| | |
|---|---|
| Dépôt blog | `github.com/Kstephane683/blog-eperformance` |
| Domaine | `blog.eperformance.pro` (fichier `CNAME`) |
| Délai de propagation | 1 à 10 minutes (cache Fastly 600 s) |

## Branches

| Branche | Rôle |
|---|---|
| `main` | Production. Ce qui est sur `main` est en ligne. |
| `blog-78-articles` | Branche de travail des 78 articles |

## Publication d'un lot

```bash
cd /home/ballo/OX6A/blog-eperformance
python3 scripts/verify-articles.py _content/articles-*.html   # doit passer
python3 _build/compose.py                                     # composition
git add -A
git commit -m "feat(articles): lot N — <périmètre>"
git push origin blog-78-articles
```

## Passage en production

Quand un lot est validé :

```bash
git checkout main
git merge blog-78-articles
git push origin main
```

## Vérification après déploiement

```bash
for u in $(curl -s https://blog.eperformance.pro/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's/<loc>//'); do
  printf "%s %s\n" "$(curl -s -o /dev/null -w '%{http_code}' "$u")" "$u"
done
```

Toutes les URL doivent répondre 200.

## Points de vigilance

**Ne jamais pousser de chemin relatif.** Le blog a des pages en sous-dossier : un `srcset` ou un `href` relatif y résout vers le sous-dossier courant. Le contrôle `verify-articles.py` le détecte.

**Les ressources partagées doivent rester identiques au site.** Après toute modification de `eperf.css` ou `eperf.js`, vérifier :

```bash
md5sum assets/css/eperf.css /home/ballo/OX6A/site-eperformance/assets/css/eperf.css
```

## Rollback

```bash
git log --oneline -5              # identifier le commit à annuler
git revert <commit>               # recommandé : l'historique reste lisible
git push origin main
```
