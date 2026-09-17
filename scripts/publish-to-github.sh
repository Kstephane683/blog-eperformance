#!/usr/bin/env bash
# Publie un lot d'articles du blog vers GitHub.
# Usage : ./scripts/publish-to-github.sh "lot N — périmètre"
set -euo pipefail

cd "$(dirname "$0")/.."
MSG="${1:-mise à jour du blog}"

echo "═══ 1. Vérification des articles ═══"
if ! python3 scripts/verify-articles.py _content/articles-*.html; then
  echo ""
  echo "  ARRÊT : au moins un article est en ÉCHEC."
  echo "  Corrigez avant de publier — le script ne fait pas de publication partielle."
  exit 1
fi

echo ""
echo "═══ 2. Composition ═══"
python3 _build/compose.py

echo ""
echo "═══ 3. Contrôle des références ═══"
python3 - <<'PY'
import re, glob, os, sys
casses = 0
for f in glob.glob('**/*.html', recursive=True):
    if '_content' in f or '.git' in f or '_templates' in f: continue
    s = open(f, encoding='utf-8').read()
    base = os.path.dirname(f)
    for attr in ('src', 'srcset', 'href'):
        for m in re.findall(attr + r'="((?!/|http|#|mailto|tel)[^"]+)"', s):
            for c in m.split(','):
                t = c.strip().split()[0].split('?')[0].split('#')[0]
                if t in ('../', '../../', '../index.html'): continue
                if t and not os.path.exists(os.path.normpath(os.path.join(base, t))):
                    print(f'  CASSÉ {f} → {attr}={t}'); casses += 1
print(f'  {casses} référence(s) cassée(s)')
sys.exit(1 if casses else 0)
PY

echo ""
echo "═══ 4. Commit et push ═══"
git add -A
if git diff --cached --quiet; then
  echo "  rien à publier"
  exit 0
fi
git commit -m "$MSG"
git push origin blog-78-articles

echo ""
echo "  Publié sur la branche blog-78-articles."
echo "  Pour passer en production : git checkout main && git merge blog-78-articles && git push origin main"
