# Blog ePerformance — blog.eperformance.pro

Blog SEO d'ePerformance (par K. STEPHANE, Abidjan, Côte d'Ivoire).
Stratégie d'acquisition rentable, création de sites web professionnels et SEO local.

## Déploiement (GitHub Pages)

1. Créer un dépôt GitHub nommé `blog-eperformance` (public).
2. Pousser tout le contenu de ce dossier à la racine du dépôt.
3. Settings → Pages → Source : branche `main` / dossier `/root`.
4. Ajouter un CNAME `blog.eperformance.pro` (déjà présent dans le dépôt).
5. Chez le registraire de `eperformance.pro`, créer un enregistrement CNAME :
   ```
   blog  CNAME  <username>.github.io.
   ```
6. Attendre 5–30 min pour la propagation DNS.
7. Vérifier : `https://blog.eperformance.pro/` doit servir le `index.html`.

## Structure

```
blog-eperformance/
├── index.html               → Accueil du blog
├── CNAME                    → blog.eperformance.pro
├── robots.txt               → Autorisation + moteurs IA
├── sitemap.xml              → Sitemap XML
├── rss.xml                  → Flux RSS
├── .gitignore               → Fichiers ignorés par Git
├── README.md                → Ce fichier
├── a-propos/index.html      → Page auteur (E-E-A-T)
├── contact/index.html       → Contact / WhatsApp
├── acquisition/index.html   → Pilier "Acquisition"
├── site-web/index.html      → Pilier "Site Web"
├── seo/index.html           → Pilier "SEO"
├── business/index.html      → Pilier "Business"
├── articles/                → Articles complets (URL /articles/<slug>/)
│   ├── calculer-cac-cote-ivoire/index.html
│   ├── site-web-professionnel-abidjan-guide/index.html
│   └── seo-local-abidjan-guide/index.html
├── _templates/              → Templates et guide
│   └── article-template.html
└── assets/
    ├── css/style.css        → Charte graphique ePerformance
    ├── js/main.js           → Interactions légères
    └── img/                 → Logos, OG images
```

## Guide d'ajout d'articles

Voir `GUIDE-AJOUT-ARTICLES.md` à la racine de l'archive livrée.

## Rapport final

Voir `RAPPORT-FINAL.md` à la racine de l'archive livrée.

## Stack

- HTML statique (pas de framework JS) → Core Web Vitals optimaux
- Aucune dépendance build, déploiement direct sur GitHub Pages
- GA4 + Microsoft Clarity + Meta Pixel (même IDs que le site principal)
- Schema.org JSON-LD complet sur chaque page
