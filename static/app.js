(() => {
  const cards = [...document.querySelectorAll('.card')];
  const q = document.getElementById('q');
  const empty = document.getElementById('empty');
  let cat = 'all';

  function apply() {
    const term = q.value.trim().toLowerCase();
    let shown = 0;
    cards.forEach(c => {
      const ok = (cat === 'all' || c.dataset.cat === cat) && c.dataset.text.includes(term);
      c.hidden = !ok;
      if (ok) shown++;
    });
    empty.hidden = shown > 0;
  }

  q.addEventListener('input', apply);
  document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    cat = b.dataset.cat;
    apply();
  }));

  // El iframe de YouTube solo se crea al hacer clic (la página carga más rápido)
  document.querySelectorAll('.thumb').forEach(btn => btn.addEventListener('click', () => {
    const f = document.createElement('iframe');
    f.src = `https://www.youtube-nocookie.com/embed/${btn.dataset.id}?autoplay=1&rel=0`;
    f.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture; fullscreen';
    f.allowFullscreen = true;
    f.title = btn.getAttribute('aria-label');
    btn.replaceWith(f);
    f.parentElement.classList.add('playing');
  }));
})();
