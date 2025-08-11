
/* ================================ */
/* /static/js/appertivo.js          */
/* ================================ */
// Vanilla JS: intersection observers, counters, and minor UX niceties.
(function(){
  // Guard reduced motion
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Reveal on scroll
  if(!prefersReduced){
    const io = new IntersectionObserver((entries)=>{
      for(const e of entries){ if(e.isIntersecting){ e.target.classList.add('inview'); io.unobserve(e.target); } }
    },{threshold:0.15});
    document.querySelectorAll('[data-animate]')?.forEach(el=>io.observe(el));
  }

  // Description counter (delegated; works after HTMX swaps)
  function bindCounters(root){
    const desc = root.querySelector('#id_description');
    const out = root.querySelector('#desc-count');
    if(desc && out){
      const update=()=>{ out.textContent = (desc.value||'').length; };
      desc.addEventListener('input', update); update();
    }
  }
  bindCounters(document);

  // Rebind behaviors after HTMX swaps
  document.body.addEventListener('htmx:afterSwap', (ev)=>{
    bindCounters(ev.target || document);
    // Re-attach observers for any new nodes
    if(!prefersReduced){
      document.querySelectorAll('[data-animate]:not(.inview)')?.forEach(el=>{
        el.style.willChange = 'opacity, transform';
      });
    }
  });

  // Minor button press pop (accessible, non-essential)
  document.addEventListener('click', (e)=>{
    const b = e.target.closest('.btn');
    if(!b) return; b.animate([{transform:'translateY(0)'},{transform:'translateY(1px)'},{transform:'translateY(0)'}],{duration:120});
  });
})();
