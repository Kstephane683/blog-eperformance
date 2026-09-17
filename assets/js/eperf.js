/* ==========================================================================
   ePerformance — Interactions
   assets/js/eperf.js

   Vanilla, sans dépendance. ~4 Ko non compressé.
   - Thème clair/sombre persistant (le thème initial est posé inline dans <head>
     pour éviter tout FOUC ; ici on ne gère que le basculement)
   - Révélations à l'entrée dans le viewport (IntersectionObserver)
   - En-tête condensé au défilement
   - Menu mobile accessible (Échap, piège de focus, aria-expanded)
   - Décomptes animés sur les bandeaux d'indicateurs

   Règle : aucune animation n'est nécessaire à la lisibilité du contenu.
   Le contenu est visible par défaut ; le JS ne fait qu'ajouter.
   ========================================================================== */

(function () {
  'use strict';

  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ----------------------------------------------------------------------
     THÈME
     Le script inline de <head> a déjà posé data-theme. Ici : basculement,
     persistance, mise à jour de aria-pressed et de theme-color.
     ---------------------------------------------------------------------- */
  var STORAGE_KEY = 'eperf-theme';

  function currentTheme() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute('content', theme === 'dark' ? '#08080c' : '#fdfcfa');
    }

    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      var isDark = theme === 'dark';
      btn.setAttribute('aria-pressed', String(isDark));
      var label = isDark ? 'Activer le thème clair' : 'Activer le thème sombre';
      btn.setAttribute('aria-label', label);
      btn.setAttribute('title', label);
    });
  }

  function initTheme() {
    applyTheme(currentTheme());

    document.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-theme-toggle]');
      if (!btn) return;

      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next);

      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (err) {
        /* Mode privé ou stockage saturé : le thème s'applique pour la session
           sans être mémorisé. Aucune raison d'interrompre l'utilisateur. */
      }
    });
  }

  /* ----------------------------------------------------------------------
     RÉVÉLATIONS
     Les éléments .reveal passent à .is-visible en entrant dans le viewport.
     Pas de JS ou mouvement réduit : ils sont visibles d'emblée (voir CSS).
     ---------------------------------------------------------------------- */
  function initReveal() {
    var targets = document.querySelectorAll('.reveal');
    if (!targets.length) return;

    if (reduceMotion.matches || !('IntersectionObserver' in window)) {
      targets.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    targets.forEach(function (el) { observer.observe(el); });
  }



  /* ----------------------------------------------------------------------
     RÉVÉLATION MOT PAR MOT DES TITRES

     Chaque mot est enveloppé dans un masque (overflow:hidden) et décalé
     vers le bas ; le passage de .words-in le fait remonter.

     Deux précautions qui ne sont pas négociables :

     1. On ne touche JAMAIS à l'opacité. Un élément à opacity:0 n'est pas
        candidat au LCP — c'est le défaut qui a coûté 0,65 s au LCP de la
        page d'accueil à la phase 2. Un élément simplement décalé, lui,
        reste peint et reste candidat.

     2. Un vrai nœud texte sépare les mots dans le DOM. Un margin-left
        donnerait le même rendu mais ferait lire « Lesprix » aux lecteurs
        d'écran, et un copier-coller perdrait les espaces.

     Si le mouvement est réduit ou si le JS échoue, le titre reste intact :
     on ne découpe que lorsque l'animation peut réellement se jouer.
     ---------------------------------------------------------------------- */
  function initWordReveal() {
    if (reduceMotion.matches) return;

    var titres = document.querySelectorAll('h1, h2');
    if (!titres.length) return;

    // Découpe récursivement, pour préserver <em>, <strong>, <a> dans les titres
    function decouper(noeud) {
      var enfants = Array.prototype.slice.call(noeud.childNodes);
      enfants.forEach(function (enfant) {
        if (enfant.nodeType === 3) {
          var mots = enfant.nodeValue.split(/(\s+)/);
          var fragment = document.createDocumentFragment();
          mots.forEach(function (morceau) {
            if (morceau === '') return;
            if (/^\s+$/.test(morceau)) {
              fragment.appendChild(document.createTextNode(' '));
              return;
            }
            var masque = document.createElement('span');
            masque.className = 'word-mask';
            var mot = document.createElement('span');
            mot.className = 'word';
            mot.textContent = morceau;
            masque.appendChild(mot);
            fragment.appendChild(masque);
          });
          noeud.replaceChild(fragment, enfant);
        } else if (enfant.nodeType === 1 && enfant.tagName !== 'BR') {
          decouper(enfant);
        }
      });
    }

    var aObserver = [];

    titres.forEach(function (titre) {
      // Un titre déjà dans le viewport au chargement (le h1 du hero) est
      // révélé sans attendre : l'animer depuis le bas au premier rendu
      // serait perçu comme un sursaut, et retarderait la lecture.
      var dejaVisible = titre.getBoundingClientRect().top < window.innerHeight * 0.9;

      decouper(titre);

      var mots = titre.querySelectorAll('.word');
      if (!mots.length) return;

      Array.prototype.forEach.call(mots, function (mot, i) {
        // Cascade plafonnée : au-delà de 12 mots, un délai croissant
        // rendrait la fin de la phrase pénible à attendre.
        mot.style.transitionDelay = Math.min(i, 12) * 42 + 'ms';
      });

      if (dejaVisible) {
        // Rendu au frame suivant, pour que la transition ait un état de départ
        window.requestAnimationFrame(function () {
          window.requestAnimationFrame(function () {
            titre.classList.add('words-in');
          });
        });
      } else {
        aObserver.push(titre);
      }
    });

    if (!aObserver.length) return;

    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (!entree.isIntersecting) return;
        entree.target.classList.add('words-in');
        observateur.unobserve(entree.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.15 });

    aObserver.forEach(function (t) { observateur.observe(t); });
  }

  /* ----------------------------------------------------------------------
     EN-TÊTE CONDENSÉ
     Un seul écouteur, passif, qui ne touche au DOM que sur changement d'état.
     ---------------------------------------------------------------------- */
  function initHeader() {
    var header = document.querySelector('.site-header');
    if (!header) return;

    var lastState = null;
    var ticking = false;

    function update() {
      var scrolled = window.scrollY > 12;
      if (scrolled !== lastState) {
        header.classList.toggle('is-scrolled', scrolled);
        lastState = scrolled;
      }
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }, { passive: true });

    update();
  }

  /* ----------------------------------------------------------------------
     MENU MOBILE
     Échap pour fermer, aria-expanded synchronisé, focus renvoyé au bouton,
     et le panneau est retiré de l'ordre de tabulation quand il est fermé.
     ---------------------------------------------------------------------- */
  function initNav() {
    var toggle = document.querySelector('.nav-toggle');
    var nav = document.querySelector('.nav');
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      /* inert retire le sous-arbre du focus et de l'arbre d'accessibilité
         quand le menu est fermé — évite les liens hors écran focalisables. */
      if (open) {
        nav.removeAttribute('inert');
      } else {
        nav.setAttribute('inert', '');
      }
    }

    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', nav.id || 'primary-nav');
    setOpen(false);

    toggle.addEventListener('click', function () {
      setOpen(!nav.classList.contains('is-open'));
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });

    /* Au passage en desktop, le panneau redevient une barre statique */
    var desktop = window.matchMedia('(min-width: 961px)');
    function sync(e) {
      if (e.matches) {
        nav.classList.remove('is-open');
        nav.removeAttribute('inert');
        toggle.setAttribute('aria-expanded', 'false');
      } else if (!nav.classList.contains('is-open')) {
        nav.setAttribute('inert', '');
      }
    }
    desktop.addEventListener('change', sync);
    sync(desktop);
  }

  /* ----------------------------------------------------------------------
     DÉCOMPTES
     Uniquement si le mouvement n'est pas réduit. La valeur finale est écrite
     dans le HTML, donc elle reste correcte sans JS.
     ---------------------------------------------------------------------- */
  function initCounters() {
    var counters = document.querySelectorAll('[data-count]');
    if (!counters.length || reduceMotion.matches || !('IntersectionObserver' in window)) return;

    function run(el) {
      var target = parseFloat(el.getAttribute('data-count'));
      if (isNaN(target)) return;

      var suffix = el.getAttribute('data-suffix') || '';
      var prefix = el.getAttribute('data-prefix') || '';
      var duration = 1100;
      var start = null;

      function step(now) {
        if (start === null) start = now;
        var progress = Math.min((now - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var value = Math.round(target * eased);
        el.textContent = prefix + value.toLocaleString('fr-FR') + suffix;
        if (progress < 1) window.requestAnimationFrame(step);
      }

      window.requestAnimationFrame(step);
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        run(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.4 });

    counters.forEach(function (el) { observer.observe(el); });
  }

  /* ----------------------------------------------------------------------
     ANNÉE COURANTE
     ---------------------------------------------------------------------- */
  function initYear() {
    document.querySelectorAll('[data-year]').forEach(function (el) {
      el.textContent = String(new Date().getFullYear());
    });
  }

  /* ---------------------------------------------------------------------- */
  function init() {
    root.classList.remove('no-js');
    initTheme();
    initReveal();
    initWordReveal();
    initHeader();
    initNav();
    initCounters();
    initYear();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
