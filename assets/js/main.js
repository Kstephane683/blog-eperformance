/* ============================================================
   BLOG ePERFORMANCE — Interactions légères
   ============================================================ */
(function(){
  'use strict';

  // Header sticky shadow on scroll
  const header = document.getElementById('header');
  if (header){
    const onScroll = () => {
      if (window.scrollY > 12) header.classList.add('scrolled');
      else header.classList.remove('scrolled');
    };
    window.addEventListener('scroll', onScroll, { passive:true });
    onScroll();
  }

  // Mobile menu
  const burger = document.getElementById('burgerBtn');
  const overlay = document.getElementById('overlay');
  const closeBtn = document.getElementById('closeBtn');
  const openMenu = () => { if (overlay) overlay.classList.add('open'); };
  const closeMenu = () => { if (overlay) overlay.classList.remove('open'); };
  if (burger) burger.addEventListener('click', openMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) closeMenu(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });

  // Copy share URL
  window.sharePage = function(platform){
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);
    const map = {
      whatsapp: `https://wa.me/?text=${title}%20${url}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
      twitter: `https://twitter.com/intent/tweet?text=${title}&url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      copy: null
    };
    if (platform === 'copy'){
      navigator.clipboard.writeText(window.location.href).then(() => {
        const btn = document.querySelector('[data-share="copy"]');
        if (btn){ const original = btn.innerHTML; btn.innerHTML = '<i class="fa-solid fa-check"></i>'; setTimeout(()=>{btn.innerHTML=original;}, 1800); }
      });
      return false;
    }
    if (map[platform]) window.open(map[platform], '_blank', 'noopener,noreferrer');
    return false;
  };

  // Active nav link
  const path = window.location.pathname.replace(/\/+$/, '').replace(/^\/+/, '/');
  document.querySelectorAll('.nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    if (href === '/' && (path === '' || path === '/')) a.classList.add('active');
    else if (href !== '/' && path.startsWith(href.replace(/\/+$/,''))) a.classList.add('active');
  });

})();
