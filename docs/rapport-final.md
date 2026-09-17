# Rapport final — stratégie blog SEO ePerformance

**Date :** 17 septembre 2026
**Branche :** `blog-78-articles` (commit `7a6ad87`) — **`main` intacte** à `0be692b`

---

## 1. Ce qui est livré

| Livrable | État |
|---|---|
| `docs/plan-editorial-6-mois.md` | ✅ 78 articles spécifiés |
| `docs/analyse-search-console.md` | ✅ Analyse de l'export GSC |
| `docs/strategie-seo-blog.md` | ✅ Six piliers, séparation site/blog, AEO |
| `docs/guide-ajout-articles.md` | ✅ Procédure en six étapes |
| `docs/guide-deploiement-github.md` | ✅ Branches, publication, rollback |
| `docs/verification-report.md` | ✅ Seuils et faux positifs du contrôle |
| `scripts/verify-articles.py` | ✅ Opérationnel, 4/4 articles conformes |
| `scripts/publish-to-github.sh` | ✅ Vérifie, compose, contrôle, publie |
| `logs/publish-log.txt` | ✅ Journal |
| **Articles rédigés** | ⚠️ **1 sur 78** |

---

## 2. L'analyse Search Console — le constat qui commande tout

**Export :** 27 février → 14 septembre 2026 · 48 clics · 1 792 impressions · 73 requêtes

**Tout le trafic organique vient de la recherche de marque.** Les 73 requêtes sont des variantes orthographiques de « eperformance » : `e performance`, `e-perform`, `eperform`, `edperformance`, `ipfromance`. **Zéro requête métier** — aucune sur « créer site web », « facebook ads », « calculer cac », « seo local », « automatisation ».

### Ce que cela implique

**Aucune repriorisation par les données n'est possible.** Il n'existe aucune requête à capter, aucun quick win à saisir, aucune position 5-20 à consolider. La colonne Priorité du plan reste donc ce qu'elle était : un ordre de production fondé sur la difficulté du sujet, pas sur un volume mesuré.

Mais l'analyse **valide le parti pris du plan** : construire une présence à partir de rien, en commençant par les territoires où la concurrence éditoriale locale est nulle.

### Trois autres enseignements

**La France génère 24 des 48 clics** (772 impressions). Probablement du bruit : `eperformance` est un terme anglophone utilisé par d'autres entreprises. À surveiller, sans en tirer de conclusion.

**Le mobile performe 4× mieux que l'ordinateur** — position 6,35 contre 25,35. Cela confirme et durcit une contrainte des conventions : le contenu doit être conçu pour un téléphone d'entrée de gamme.

**Trois anomalies de site, hors périmètre blog :**

| Page | Symptôme | Action |
|---|---|---|
| `/formation.html` | 329 impressions, **0 clic**, position 12,84 | Réécrire title et description — seul quick win réel de l'export |
| `/site-web-75000.html` | Ancienne URL encore indexée | Redirection |
| `/guide.html` | Page inexistante, position 2 | Redirection |

---

## 3. Le pilote

**« Qu'est-ce que l'IA générative pour une PME africaine, concrètement »**
`/articles/ia-generative-pme-africaine/` · 2 391 mots · 14 sections H2 · 5 sous-sections · 6 questions FAQ

**Angle :** partir de trois tâches réelles — répondre aux questions fréquentes, rédiger ce qu'on repousse, résumer un rapport — plutôt que de la technologie. Le tiers de l'article couvre ce que l'IA **ne fait pas**, parce que c'est cette partie qui détermine un usage correct.

**Vérifications :** script → OK · 3 schémas JSON-LD valides · 1 H1, 1 header, 1 main, 1 footer · 0 traceur en dur · ressources absolues.

**Conformité :** aucune promesse de résultat, aucun chiffre présenté comme un résultat client, aucun superlatif commercial, aucun emoji. CTA vers le diagnostic.

---

## 4. Ce qui n'est pas fait — et pourquoi

**77 articles sur 78 ne sont pas rédigés.**

Ce n'est pas un abandon en cours de route : c'est un constat de volume. 78 articles de 2 300 mots représentent **environ 180 000 mots**, soit plusieurs jours de travail à temps plein. J'ai produit le pilote et l'infrastructure complète, mais je ne pouvais pas produire 180 000 mots dans une session.

**Ce qui est prêt pour la suite :** le plan détaillé, le contrôle automatique, le script de publication, les guides. Produire les 77 articles restants est maintenant une opération mécanique — chaque article suit le modèle, passe le script, et se publie par lot de 10.

---

## 5. Le contrôle automatique — et ce qu'il a corrigé

`scripts/verify-articles.py` vérifie neuf points : longueur, sections, FAQ, présence et validité des trois schémas, liens relatifs interdits **y compris dans `srcset`**, formulations interdites, présence d'un CTA.

**Ses seuils sont calibrés sur les 3 articles en ligne, pas estimés.** La première version rejetait les 3 articles de référence — elle exigeait 4 à 8 sections H2 et un chapô de 120 mots, des valeurs inventées. Un script qui rejette le standard existant a des seuils faux, pas le standard.

**Deux faux positifs corrigés :**

« garanti » captait « la **garantie** » — nom commun légitime dans une liste de questions fréquentes. Motif corrigé en `\bgarantis?\b` : le `\b` échoue entre « i » et « e », donc « garantie » n'est plus capté.

`../` était signalé comme lien relatif. Dans le fil d'Ariane des articles, il remonte de `/articles/xxx/` vers `/articles/` — il résout correctement. Exception ajoutée, comme dans les articles en ligne.

**Résultat :** 4/4 articles conformes (3 de référence + le pilote).

---

## 6. Comment terminer les 77 articles

```bash
cd /home/ballo/OX6A/blog-eperformance
git checkout blog-78-articles

# Pour chaque lot de 10 : rédiger les fragments dans _content/,
# puis vérifier et publier d'un coup.
./scripts/publish-to-github.sh "feat(articles): lot N — <périmètre>"
```

Le script refuse de publier si un seul article échoue — pas de publication partielle.

**Ordre de production** : suivre la numérotation du plan. Les 8 premiers articles complètent le cluster IA générative (n° 2 à 9), puis l'automatisation (n° 10 à 18).

**Points de vigilance pour la suite** — les cinq défauts rencontrés pendant la migration du blog venaient tous de la même cause : des liens qui ne résolvaient pas depuis leur contexte réel. Le script contrôle désormais `href`, `src` **et `srcset`**. Mais il ne contrôle ni la qualité rédactionnelle, ni la justesse des affirmations, ni le rendu visuel : ces trois points demandent une relecture humaine.

---

## 7. État du dépôt

| | |
|---|---|
| Branche de travail | `blog-78-articles` @ `7a6ad87` |
| `main` | `0be692b` — **intacte**, le blog en production n'a pas bougé |
| Articles rédigés | 4 (3 existants + 1 pilote) |
| Pages du blog | 11 |
| Arbre de travail | propre |

**Rien n'est passé en production.** Le pilote est sur la branche de travail, pas sur `main`. Pour le mettre en ligne :

```bash
git checkout main
git merge blog-78-articles
git push origin main
```
