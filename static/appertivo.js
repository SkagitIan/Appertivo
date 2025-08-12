/* ================================
   /static/js/appertivo.js
   Vanilla JS for Appertivo forms & UI
   - Intersection observers
   - Counters, date chips
   - CTA reveal/focus/required
   - Image dropzone
   - Keyboard shortcuts
   - HTMX-safe re-init
   ================================ */
(function(){
  'use strict';

  // -------------------------------
  // Helpers
  // -------------------------------
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  const $  = (sel, root=document) => root.querySelector(sel);
  const clamp = (n, min, max)=> Math.max(min, Math.min(max, n));
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // -------------------------------
  // Reveal-on-scroll (decorative)
  // -------------------------------
  if(!prefersReduced){
    const io = new IntersectionObserver((entries)=>{
      for(const e of entries){
        if(e.isIntersecting){
          e.target.classList.add('inview');
          io.unobserve(e.target);
        }
      }
    }, { threshold: 0.15 });
    document.querySelectorAll('[data-animate]')?.forEach(el => io.observe(el));
  }

  // -------------------------------
  // Title/Description counters
  // -------------------------------
  function bindCounters(root){
    const title = $('#id_title', root);
    const desc  = $('#id_description', root);
    const tOut  = $('#title-count', root);
    const dOut  = $('#desc-count', root);

    if (title && tOut && !title.dataset.boundCounter){
      const update = ()=>{ tOut.textContent = `${clamp(title.value.length,0,60)}/60`; };
      title.addEventListener('input', update);
      update();
      title.dataset.boundCounter = '1';
    }
    if (desc && dOut && !desc.dataset.boundCounter){
      const update = ()=>{ dOut.textContent = `${clamp((desc.value||'').length,0,250)}/250`; };
      desc.addEventListener('input', update);
      update();
      desc.dataset.boundCounter = '1';
    }
  }

  // -------------------------------
  // Price formatting (display only)
  // -------------------------------
  function bindPrice(root){
    const input = $('#id_price', root);
    if(!input || input.dataset.boundPrice) return;
    input.addEventListener('blur', ()=>{
      const v = parseFloat(input.value);
      if(!isNaN(v)) input.value = v.toFixed(2);
    });
    input.dataset.boundPrice = '1';
  }

  // -------------------------------
  // CTA segmented control
  // NOTE: This is a static JS file; we can't use Django template vars.
  // We infer the radio "name" and scope from the CTA container itself.
  // -------------------------------
  // ---------- CTA segmented control (robust, no aria-label dependency) ----------
function bindCTA(root){
  const form = root.closest?.('form') || root.querySelector?.('#special-form') || root;
  if (!form) return;

  const labels = form.querySelectorAll('label[data-cta]');
  if (!labels.length) return;

  const radios = form.querySelectorAll('input[type="radio"].btn-check');
  if (!radios.length) return;

  if (form.dataset.ctaBound === '1') return;
  form.dataset.ctaBound = '1';

  const groups = {};
  const inputs = {};
  const getGroupId = (val) => `group-${val}`;

  radios.forEach(r => {
    const id = getGroupId(r.value);
    const g = form.querySelector(`#${CSS.escape(id)}`);
    if (g){
      groups[r.value] = g;
      inputs[r.value] = g.querySelector('input,textarea,select');
    }
  });

  function showGroup(key, focus=false){
    Object.keys(groups).forEach(k => {
      const g = groups[k], inp = inputs[k];
      if (!g) return;
      g.classList.add('d-none');
      g.style.opacity = 0;
      if (inp){ inp.disabled = true; inp.required = false; }
    });

    labels.forEach(l => l.classList.remove('btn-orange'));
    form.querySelector(`label[data-cta="${key}"]`)?.classList.add('btn-orange');

    const g = groups[key], inp = inputs[key];
    if (g){
      g.classList.remove('d-none');
      requestAnimationFrame(()=>{
        g.style.transition = 'opacity .18s ease';
        g.style.opacity = 1;
      });
      if (inp){
        inp.disabled = false;
        inp.required = true;
        if (focus){ setTimeout(()=>{ inp.focus(); inp.select?.(); }, 50); }
      }
    }
  }

  function sync(focus=false){
    const r = Array.from(radios).find(x => x.checked);
    if (r) showGroup(r.value, focus);
  }

  labels.forEach(l => {
    l.addEventListener('click', () => {
      const val = l.getAttribute('data-cta');
      const r = Array.from(radios).find(x => x.value === val);
      if (r){ r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true})); }
    });
  });

  radios.forEach(r => r.addEventListener('change', ()=>sync(true)));

  if (![...radios].some(r => r.checked)) {
    const first = [...radios].find(r => groups[r.value]);
    if (first) first.checked = true;
  }

  sync(false);
}


  // -------------------------------
  // Date helpers
  // -------------------------------
  function bindDates(root){
    const start   = $('#id_start_date', root);
    const end     = $('#id_end_date', root);
    const startBtn= $('#start-date-button', root);
    const endBtn  = $('#end-date-button', root);
    const help    = $('#date-help', root);

    function attach(input, btn){
      if(!(input && btn) || btn.dataset.boundPicker) return;
      btn.addEventListener('click', ()=> input.showPicker ? input.showPicker() : input.click());
      btn.dataset.placeholder = btn.textContent;
      input.addEventListener('change', ()=>{
        btn.textContent = input.value || btn.dataset.placeholder;
        validate();
      });
      btn.textContent = input.value || btn.textContent;
      btn.dataset.boundPicker = '1';
    }
    attach(start, startBtn);
    attach(end, endBtn);

    function setChip(type){
      const today = new Date();
      const pad = n => String(n).padStart(2,'0');
      const toISO = d => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
      if(!start || !end) return;

      if(type === 'today'){ start.value = toISO(today); end.value = toISO(today); }
      if(type === 'plus3'){ const e = new Date(today); e.setDate(e.getDate()+3); start.value = toISO(today); end.value = toISO(e); }
      if(type === 'plus7'){ const e = new Date(today); e.setDate(e.getDate()+7); start.value = toISO(today); end.value = toISO(e); }

      start.dispatchEvent(new Event('change')); end.dispatchEvent(new Event('change'));
      validate();
    }

    function validate(){
      if(!(start && end && help)) return;
      if(start.value && end.value && end.value < start.value){
        help.textContent = 'End date must be on or after the start date.';
        help.classList.add('text-danger');
      } else {
        help.textContent = '';
        help.classList.remove('text-danger');
      }
    }

    $$('[data-datechip]', root).forEach(b => {
      if (!b.dataset.boundChip){
        b.addEventListener('click', ()=> setChip(b.dataset.datechip));
        b.dataset.boundChip = '1';
      }
    });

    start?.addEventListener('change', validate);
    end  ?.addEventListener('change', validate);
  }

  // -------------------------------
  // Image dropzone + preview
  // -------------------------------
  function bindImage(root){
    const input  = $('#id_image', root);
    const dz     = $('#image-dropzone', root);
    const img    = $('#image-preview', root);
    const shell  = $('#image-preview-shell', root);
    const reset  = $('#image-reset', root);
    if(!(input && dz && img && shell && reset) || dz.dataset.imgBound === '1') return;

    function showPreview(file){
      const okType = /image\/(jpeg|png)/.test(file.type);
      const okSize = file.size <= 5 * 1024 * 1024;
      if(!okType || !okSize){
        shell.classList.add('border','border-danger');
        shell.setAttribute('title','Use JPG/PNG under 5MB');
        return;
      }
      const url = URL.createObjectURL(file);
      img.src = url;
      img.classList.remove('d-none');
      reset.hidden = false;
    }

    input.addEventListener('change', (e)=>{
      const file = e.target.files?.[0];
      if(file) showPreview(file);
    });

    function consume(e){ e.preventDefault(); e.stopPropagation(); }
    ['dragenter','dragover','dragleave','drop'].forEach(ev => dz.addEventListener(ev, consume));
    dz.addEventListener('dragover', ()=> dz.classList.add('border','border-teal'));
    dz.addEventListener('dragleave', ()=> dz.classList.remove('border','border-teal'));
    dz.addEventListener('drop', (e)=>{
      const file = e.dataTransfer.files?.[0];
      if(file){ input.files = e.dataTransfer.files; showPreview(file); }
      dz.classList.remove('border','border-teal');
    });

    reset.addEventListener('click', ()=>{
      input.value = '';
      img.src = '';
      img.classList.add('d-none');
      reset.hidden = true;
    });

    if (img.src && !img.classList.contains('d-none')) {
      reset.hidden = false;
    }

    dz.dataset.imgBound = '1';
  }

  // -------------------------------
  // Keyboard shortcuts
  // -------------------------------
  function bindShortcuts(){
    if (document.body.dataset.kbBound === '1') return;
    document.addEventListener('keydown', (e)=>{
      const metaEnter = (e.ctrlKey || e.metaKey) && e.key === 'Enter';
      const shiftP    = e.shiftKey && (e.key.toLowerCase() === 'p');
      if(metaEnter){ $('#special-form')?.requestSubmit(); }
      if(shiftP){ $('#btn-refresh-preview')?.click(); }
    });
    document.body.dataset.kbBound = '1';
  }

  // -------------------------------
  // Button press micro-animation
  // -------------------------------
  function bindButtonPop(){
    if (document.body.dataset.btnPopBound === '1') return;
    document.addEventListener('click', (e)=>{
      const b = e.target.closest('.btn');
      if(!b) return;
      b.animate(
        [{transform:'translateY(0)'},{transform:'translateY(1px)'},{transform:'translateY(0)'}],
        {duration:120}
      );
    });
    document.body.dataset.btnPopBound = '1';
  }

  // -------------------------------
  // Init (idempotent on HTMX swaps)
  // -------------------------------
  function init(root=document){
    // Scope to the form if present; otherwise use root
    const formScope = $('#special-form', root) || root;
    bindCounters(formScope);
    bindPrice(formScope);
    bindDates(formScope);
    bindCTA(formScope);
    bindImage(formScope);
    bindShortcuts();
    bindButtonPop();
  }

  // First load
  document.addEventListener('DOMContentLoaded', ()=> init(document));

  // Re-init after HTMX swaps (only when the form area changed)
// appertivo.js
document.body.addEventListener('htmx:afterSwap', (ev)=>{
  if (ev?.target?.closest?.('#special-form-container') || ev?.target?.closest?.('#special-preview-container')) {
    // if you need CTA/date bindings inside preview editors, call init(ev.target)
    // init(ev.target);  // uncomment if you include CTA bits in preview editors later
  }
});

})();
