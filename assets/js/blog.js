/* ==========================================================================
   Blog ePerformance — Interactions éditoriales
   assets/js/blog.js

   Seul script propre au blog. Il contient ce qui n'existe pas sur le site :
     · le partage d'article
     · la barre de progression de lecture
     · le sommaire de l'article avec section active

   Tout le reste (thème, menu, défilement, révélations, compteurs) vient
   d'eperf.js, la MÊME copie que le site — c'est ce qui garantit que les
   deux se comportent à l'identique.

   Vérification d'identité : assets/js/eperf.js et assets/js/consent.js
   doivent rester identiques au bit près à ceux du site. Ne pas les modifier
   ici : toute correction se fait côté site puis se recopie.
   ========================================================================== */

(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ----------------------------------------------------------------------
     PARTAGE D'ARTICLE
     ---------------------------------------------------------------------- */
  window.sharePage = function (platform) {
    var url = encodeURIComponent(window.location.href);
    var titre = encodeURIComponent(document.title);
    var cible = '';

    if (platform === 'whatsapp') {
      cible = 'https://api.whatsapp.com/send?text=' + titre + '%20' + url;
    } else if (platform === 'linkedin') {
      cible = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
    } else if (platform === 'twitter' || platform === 'x') {
      cible = 'https://twitter.com/intent/tweet?text=' + titre + '&url=' + url;
    } else if (platform === 'facebook') {
      cible = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    } else if (platform === 'copy') {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(window.location.href).then(function () {
          var btn = document.querySelector('[data-share="copy"]');
          if (!btn) return;
          var avant = btn.textContent;
          btn.textContent = 'Lien copié';
          setTimeout(function () { btn.textContent = avant; }, 2000);
        });
      }
      return false;
    }

    if (cible) window.open(cible, '_blank', 'noopener,width=640,height=560');
    return false;
  };

  /* ----------------------------------------------------------------------
     BARRE DE PROGRESSION DE LECTURE

     Le calcul se fait sur la hauteur réelle de l'article, pas du document :
     la progression atteint 100 % quand la fin de l'article est en bas de
     l'écran, ce qui correspond à ce que le lecteur perçoit.

     transform:scaleX est composé par le GPU — aucun recalcul de mise en
     page à chaque frame. Un seul écouteur, passif, throttlé par rAF.
     ---------------------------------------------------------------------- */
  function initProgress() {
    var article = document.querySelector('.article-body');
    if (!article) return;

    var barre = document.createElement('div');
    barre.className = 'reading-progress is-idle';
    barre.setAttribute('role', 'presentation');
    barre.innerHTML = '<span></span>';
    document.body.appendChild(barre);

    var remplissage = barre.querySelector('span');
    var enAttente = false;
    var dernier = -1;

    function mettreAJour() {
      enAttente = false;
      var rect = article.getBoundingClientRect();
      var hauteur = rect.height - window.innerHeight;
      // Article plus court que l'écran : rien à mesurer, la barre reste effacée
      var ratio = hauteur > 0 ? Math.min(Math.max(-rect.top / hauteur, 0), 1) : 0;

      if (Math.abs(ratio - dernier) < 0.001) return;
      dernier = ratio;

      remplissage.style.transform = 'scaleX(' + ratio + ')';
      barre.classList.toggle('is-idle', ratio <= 0.01 || ratio >= 0.995);
    }

    window.addEventListener('scroll', function () {
      if (enAttente) return;
      enAttente = true;
      window.requestAnimationFrame(mettreAJour);
    }, { passive: true });

    window.addEventListener('resize', mettreAJour, { passive: true });
    mettreAJour();
  }

  /* ----------------------------------------------------------------------
     SOMMAIRE DE L'ARTICLE

     Construit à partir des <h2> du corps. Le site n'a pas d'équivalent :
     ses pages ne sont pas des textes longs.

     L'état actif est déterminé par la position des titres par rapport au
     tiers supérieur de l'écran, plutôt que par un IntersectionObserver :
     plusieurs titres peuvent être visibles simultanément, et seul le
     dernier franchi doit être signalé comme courant.
     ---------------------------------------------------------------------- */
  function initToc() {
    var article = document.querySelector('.article-body');
    if (!article) return;

    var titres = article.querySelectorAll('h2[id], h2');
    if (titres.length < 4) return;   // en dessous, un sommaire n'aide pas

    // Les ancres doivent exister pour être cliquables
    Array.prototype.forEach.call(titres, function (t, i) {
      if (!t.id) {
        t.id = 'section-' + (i + 1);
      }
    });

    var nav = document.createElement('nav');
    nav.className = 'article-toc';
    nav.setAttribute('aria-label', 'Sommaire de l’article');

    var html = '<h2>Sommaire</h2><ol>';
    Array.prototype.forEach.call(titres, function (t) {
      html += '<li><a href="#' + t.id + '">' + t.textContent.trim() + '</a></li>';
    });
    html += '</ol>';
    nav.innerHTML = html;
    document.body.appendChild(nav);

    var liens = nav.querySelectorAll('a');
    var actif = null;
    var enAttente = false;

    function surligner() {
      enAttente = false;
      var courant = null;

      // Le titre courant est le dernier dont le haut est passé au-dessus du
      // tiers supérieur de l'écran.
      Array.prototype.forEach.call(titres, function (t) {
        if (t.getBoundingClientRect().top <= window.innerHeight * 0.34) courant = t.id;
      });

      // En bas de page, on force le dernier : sinon la dernière section ne
      // serait jamais signalée si elle est trop courte pour atteindre le seuil.
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 60) {
        courant = titres[titres.length - 1].id;
      }

      if (courant === actif) return;
      actif = courant;

      Array.prototype.forEach.call(liens, function (a) {
        if (a.getAttribute('href') === '#' + courant) {
          a.setAttribute('aria-current', 'true');
        } else {
          a.removeAttribute('aria-current');
        }
      });
    }

    window.addEventListener('scroll', function () {
      if (enAttente) return;
      enAttente = true;
      window.requestAnimationFrame(surligner);
    }, { passive: true });

    surligner();
  }

  /* ---------------------------------------------------------------------- */
  function init() {
    initProgress();
    initToc();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
