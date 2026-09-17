/* ==========================================================================
   ePerformance — Consentement et traceurs
   assets/js/consent.js

   GA4, Microsoft Clarity et Meta Pixel ne se chargent QU'APRÈS consentement
   explicite. Aujourd'hui ils se déclenchent au chargement sur toutes les
   pages, sans base légale — c'est le point A du chantier légal de la phase 2.

   Trois catégories :
     necessary   — toujours actifs (thème, préférences). Aucun traceur tiers.
     analytics   — GA4 + Clarity
     ads         — Meta Pixel

   Le choix est stocké dans localStorage sous `eperf-consent`, versionné.
   Le bandeau est réaffiché si la version change.

   Aucun traceur n'est injecté avant un choix explicite : ni « accepter par
   défaut », ni « consentement implicite par la poursuite de la navigation ».
   ========================================================================== */

(function () {
  'use strict';

  var STORAGE_KEY = 'eperf-consent';
  var VERSION = 1;   // incrémenter pour redemander le consentement

  // ---------------------------------------------------------------------
  // IDENTIFIANTS DE MESURE
  //   Repris du site existant, inchangés — seule la condition de
  //   déclenchement change.
  // ---------------------------------------------------------------------
  var GA4_ID = 'G-Z7QW8BCYQ1';
  var CLARITY_ID = 'w2e89n0biv';
  var META_PIXEL_ID = '1592627695615531';

  // ---------------------------------------------------------------------
  // LECTURE / ÉCRITURE DU CHOIX
  // ---------------------------------------------------------------------

  function readConsent() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || parsed.version !== VERSION) return null;
      return parsed;
    } catch (err) {
      return null;
    }
  }

  function writeConsent(analytics, ads) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: VERSION,
        analytics: !!analytics,
        ads: !!ads,
        date: new Date().toISOString()
      }));
    } catch (err) {
      /* Mode privé : le choix vaut pour la session sans être mémorisé. */
    }
  }

  /* Exposé pour que la politique de confidentialité et la page cookies
     puissent proposer un bouton « Gérer mes cookies ». */
  window.eperfConsent = {
    open: function () {
      var banner = document.getElementById('consent-banner');
      if (!banner) return;
      banner.hidden = false;
      var first = banner.querySelector('[data-consent]');
      if (first) first.focus();
    },
    get: readConsent
  };

  // ---------------------------------------------------------------------
  // CHARGEMENT DES TRACEURS
  //   Chaque fonction est idempotente : appeler deux fois ne charge pas
  //   deux fois le script.
  // ---------------------------------------------------------------------

  function loadAnalytics() {
    if (window.__eperfAnalyticsLoaded) return;
    window.__eperfAnalyticsLoaded = true;

    // --- Google Analytics 4 ---
    var ga = document.createElement('script');
    ga.async = true;
    ga.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    document.head.appendChild(ga);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA4_ID, { anonymize_ip: true });

    // --- Microsoft Clarity ---
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1;
      t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0];
      y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', CLARITY_ID);
  }

  function loadAds() {
    if (window.__eperfAdsLoaded) return;
    window.__eperfAdsLoaded = true;

    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return;
      n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
      t = b.createElement(e); t.async = !0;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');

    window.fbq('init', META_PIXEL_ID);
    window.fbq('track', 'PageView');
  }

  function applyConsent(consent) {
    if (consent.analytics) loadAnalytics();
    if (consent.ads) loadAds();
  }

  // ---------------------------------------------------------------------
  // BANDEAU
  // ---------------------------------------------------------------------

  function initBanner() {
    var banner = document.getElementById('consent-banner');
    if (!banner) return;

    var detail = document.getElementById('consent-detail');
    var analyticsBox = document.getElementById('consent-analytics');
    var adsBox = document.getElementById('consent-ads');

    var saved = readConsent();

    if (saved) {
      // Choix déjà exprimé : on applique en silence, sans réafficher.
      // Les écouteurs sont posés malgré tout : la page cookies rouvre ce
      // bandeau avec « Gérer mes cookies » pour revenir sur la décision.
      if (analyticsBox) analyticsBox.checked = !!saved.analytics;
      if (adsBox) adsBox.checked = !!saved.ads;
      applyConsent(saved);
    } else {
      // Aucun choix : le bandeau s'affiche, aucun traceur ne part.
      banner.hidden = false;
    }

    banner.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-consent]');
      if (!btn) return;

      var action = btn.getAttribute('data-consent');

      if (action === 'accept') {
        writeConsent(true, true);
        applyConsent({ analytics: true, ads: true });
        banner.hidden = true;

      } else if (action === 'refuse') {
        writeConsent(false, false);
        // Rien à charger : refuser est un état légitime et complet.
        banner.hidden = true;

      } else if (action === 'customize') {
        detail.hidden = false;
        var first = detail.querySelector('input:not([disabled])');
        if (first) first.focus();

      } else if (action === 'back') {
        detail.hidden = true;

      } else if (action === 'save') {
        var analytics = !!(analyticsBox && analyticsBox.checked);
        var ads = !!(adsBox && adsBox.checked);
        writeConsent(analytics, ads);
        applyConsent({ analytics: analytics, ads: ads });
        banner.hidden = true;
      }
    });

    // Échap ferme le panneau de détail sans valider de choix
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !detail.hidden) {
        detail.hidden = true;
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBanner);
  } else {
    initBanner();
  }
})();
