# Guide — ajouter un article

## 1. Choisir le sujet

Dans `docs/plan-editorial-6-mois.md`. Chaque ligne donne le titre, le mot-clé principal, les secondaires, l'intention, l'angle, le CTA, le marché et la priorité.

**Vérifier la cannibalisation** : le titre ne doit pas redoubler une tête déjà occupée (voir `docs/strategie-seo-blog.md` §2).

## 2. Rédiger le fragment

Créer `_content/articles-<slug>.html`. **Modèle absolu** : `_content/articles-calculer-cac-cote-ivoire.html`.

Le fragment contient le contenu du `<main>` uniquement :
- `.article-hero` : fil d'Ariane, `.article-category`, `<h1>`, `.lead`, `.article-meta`
- `.article-body.container-reading` : le corps
- FAQ en `<details>`/`<summary>`
- `.tags-row`, `.share-row`, `.related`
- **Trois blocs JSON-LD** : `Article`, `BreadcrumbList`, `FAQPage`

**Cibles** : 2 000 à 2 500 mots, 9 à 16 sections `h2`, 5 à 7 questions FAQ, chapô de 25 à 60 mots.

**Liens absolus obligatoires** dans `href`, `src` **et `srcset`**. Seule exception : `../` dans le fil d'Ariane.

## 3. Vérifier

```bash
python3 scripts/verify-articles.py _content/articles-<slug>.html
```

Cible : `OK` ou `WARN`. **Jamais `ÉCHEC`.**

## 4. Enregistrer dans le composeur

Ajouter une entrée dans le dict `PAGES` de `_build/compose.py` :

```python
"articles/<slug>/index.html": {
    "title": "…",              # ≤ 60 caractères
    "description": "…",        # ≤ 160 caractères
    "fragment": "articles-<slug>.html",
    "nav_active": "<pilier>",
    "breadcrumb": [("<Pilier>", "/"), ("<Titre court>", "/articles/<slug>/")],
},
```

## 5. Composer et contrôler

```bash
python3 _build/compose.py
python3 -m http.server 8011
```

Le composeur refuse d'écrire une page dont les ressources critiques manquent.

## 6. Publier

```bash
git add -A
git commit -m "feat(articles): <titre>"
git push origin blog-78-articles
```

## Rappels de conformité

- Aucune promesse de résultat, aucun chiffre présenté comme un résultat client
- Aucun « garanti », « sans blabla », « à l'aveugle », « le meilleur », « n°1 »
- Aucun emoji, aucun témoignage inventé
- Prix en FCFA
- Sur l'IA, l'automatisation et les données : décrire le principe, ne promettre aucune conformité juridique
