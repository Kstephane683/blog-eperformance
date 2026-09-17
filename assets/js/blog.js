/* ==========================================================================
   Blog ePerformance — Interactions éditoriales
   assets/js/blog.js

   Seul script propre au blog. Il ne contient QUE ce qui n'existe pas sur le
   site : le partage d'article. Tout le reste (thème, menu, défilement) vient
   d'eperf.js, la MÊME copie que le site — c'est ce qui garantit que les deux
   se comportent à l'identique.

   Vérification d'identité : assets/js/eperf.js et assets/js/consent.js
   doivent rester identiques au bit près à ceux du site. Ne pas les modifier
   ici : toute correction doit être faite côté site puis recopiée par
   _build/sync-from-site.sh.
   ========================================================================== */

(function () {
  'use strict';

  window.sharePage = function (platform) {
    var url = encodeURIComponent(window.location.href);
    var title = encodeURIComponent(document.title);
    var cible = '';

    if (platform === 'whatsapp') {
      cible = 'https://api.whatsapp.com/send?text=' + title + '%20' + url;
    } else if (platform === 'linkedin') {
      cible = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
    } else if (platform === 'twitter' || platform === 'x') {
      cible = 'https://twitter.com/intent/tweet?text=' + title + '&url=' + url;
    } else if (platform === 'facebook') {
      cible = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    } else if (platform === 'copy') {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(window.location.href).then(function () {
          var btn = document.querySelector('[data-share="copy"]');
          if (!btn) return;
          var avant = btn.getAttribute('aria-label') || btn.textContent;
          btn.textContent = 'Lien copié';
          setTimeout(function () { btn.textContent = avant; }, 2000);
        });
      }
      return false;
    }

    if (cible) window.open(cible, '_blank', 'noopener,width=640,height=560');
    return false;
  };
})();
