// All interactions are frontend previews; no booking service is connected.
const menu = document.querySelector('.menu-toggle');
menu?.addEventListener('click', () => { const open = menu.getAttribute('aria-expanded') !== 'true'; menu.setAttribute('aria-expanded', String(open)); document.querySelector('#nav-links').classList.toggle('open', open); });
let category = 'Flights';
document.querySelectorAll('[data-category]').forEach(button => button.addEventListener('click', () => { category = button.dataset.category; document.querySelectorAll('[data-category]').forEach(tab => { tab.classList.toggle('active', tab === button); tab.setAttribute('aria-pressed', String(tab === button)); }); document.querySelector('#origin-label').textContent = category === 'Hotels' ? 'Your city' : 'From'; }));
const departure = document.querySelector('#departure');
const returnDate = document.querySelector('#return');
if (departure) { const now = new Date(); const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`; departure.min = today; returnDate.min = today; departure.addEventListener('change', () => { returnDate.min = departure.value; if(returnDate.value && returnDate.value < departure.value) returnDate.value = ''; }); }
document.querySelector('#search-form')?.addEventListener('submit', event => { event.preventDefault(); const destination = document.querySelector('#destination').value.trim(); const message = document.querySelector('#search-message'); message.textContent = `${category} inspiration for ${destination}. These are sample destinations; live search is not connected yet.`; document.querySelector('#destinations').scrollIntoView({behavior:'smooth'}); });
const cards = document.querySelector('#destination-cards');
document.querySelector('.next')?.addEventListener('click', () => rotateDestinations(1));
document.querySelector('.previous')?.addEventListener('click', () => rotateDestinations(-1));
const dialog = document.querySelector('#details');
document.querySelectorAll('[data-detail]').forEach(button => button.addEventListener('click', () => { const content = document.querySelector('#detail-content'); content.replaceChildren(); const heading = document.createElement('h2'); heading.textContent = button.dataset.detail; const description = document.createElement('p'); description.textContent = `Sample package from $${button.dataset.price} per person. Explore local sights, beautiful scenery, and time to relax. This is a frontend preview, not a live booking offer.`; const link = document.createElement('a'); link.href='/api/trips'; link.className='primary'; link.textContent='Open trips JSON'; content.append(heading,description,link); dialog.showModal(); }));
document.querySelector('.close')?.addEventListener('click', () => dialog.close());
document.querySelector('#newsletter')?.addEventListener('submit', event => { event.preventDefault(); document.querySelector('#newsletter-message').textContent='Thanks for your interest! This demo does not send or store subscriptions.'; });
document.querySelector('#contact-form')?.addEventListener('submit', event => { event.preventDefault(); document.querySelector('#contact-message').textContent='Your message looks ready. Sending will be available when the contact backend is connected.'; });

let selectedClimate = 'warm';
function applyClimate(climate) {
  selectedClimate = climate;
  document.querySelectorAll('[data-climate]').forEach(element => {
    if (element.matches('button')) {
      const selected = element.dataset.climate === climate;
      element.classList.toggle('active', selected);
      element.setAttribute('aria-pressed', String(selected));
    } else if (element.matches('.destination-card')) element.hidden = element.dataset.climate !== climate;
  });
  const description = document.querySelector('#climate-description');
  if (description) description.textContent = climate === 'warm' ? 'Sunshine, golden dunes, and island escapes.' : 'Snowy mountains, glaciers, and cozy winter escapes.';
}
if (document.querySelector('.climate-picker')) {
  document.querySelectorAll('button[data-climate]').forEach(button => button.addEventListener('click', () => applyClimate(button.dataset.climate)));
  applyClimate('warm');
}
function rotateDestinations(direction) {
  const visible = [...cards.children].filter(card => !card.hidden);
  if (visible.length < 2) return;
  if (direction > 0) cards.append(visible[0]); else cards.prepend(visible[visible.length - 1]);
}
const sahara = document.querySelector('.sahara-hero');
if (sahara && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  sahara.addEventListener('pointermove', event => {
    if (event.pointerType === 'touch') return;
    const bounds = sahara.getBoundingClientRect();
    sahara.style.setProperty('--scene-x', `${((event.clientX-bounds.left)/bounds.width-.5)*18}px`);
    sahara.style.setProperty('--scene-y', `${((event.clientY-bounds.top)/bounds.height-.5)*10}px`);
  });
  sahara.addEventListener('pointerleave', () => { sahara.style.setProperty('--scene-x','0px'); sahara.style.setProperty('--scene-y','0px'); });
}

// Replace these images in static/images, or edit the paths and captions here.
const heroSlides = [
  {title: 'ISLAND ESCAPE', subtitle: 'Your Own Little Paradise', image: '/static/images/hero-island.jpg'},
  {title: 'SAHARA', subtitle: 'The Largest Hot Desert', image: '/static/images/hero-sahara.jpg', desert: true},
  {title: 'CARIBBEAN', subtitle: 'Sunshine, Sea, and Slow Days', image: '/static/images/hero-caribbean.jpg'},
  {title: 'KENYA', subtitle: 'Your Next Safari Adventure', image: '/static/images/hero-kenya.jpg'}
];
const heroIntervalMs = 5000; // Time between slides in milliseconds.
if (sahara) {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const slideRoot = sahara.querySelector('.hero-slides');
  const dots = document.querySelector('#hero-dots');
  const pause = document.querySelector('#hero-pause');
  let current = 0, timer, paused = reducedMotion.matches;
  heroSlides.forEach((slide, index) => {
    const layer = document.createElement('div');
    layer.className = 'hero-slide';
    layer.style.backgroundImage = `linear-gradient(180deg,#35201425,#35201440), url("${slide.image}")`;
    slideRoot.append(layer);
    const dot = document.createElement('button');
    dot.type = 'button'; dot.setAttribute('aria-label', `Show ${slide.title}`);
    dot.addEventListener('click', () => { showSlide(index); schedule(); });
    dots.append(dot);
  });
  function showSlide(index) {
    current = (index + heroSlides.length) % heroSlides.length;
    const slide = heroSlides[current];
    [...slideRoot.children].forEach((layer, i) => layer.classList.toggle('active', i === current));
    [...dots.children].forEach((dot, i) => dot.setAttribute('aria-pressed', String(i === current)));
    sahara.classList.toggle('show-desert', !!slide.desert);
    sahara.querySelector('h1').textContent = slide.title;
    sahara.querySelector('.hero-copy .script').textContent = slide.subtitle;
  }
  function schedule() {
    clearInterval(timer);
    if (!paused && !document.hidden && !sahara.matches(':hover') && !sahara.contains(document.activeElement))
      timer = setInterval(() => showSlide(current + 1), heroIntervalMs);
    pause.textContent = paused ? 'Play' : 'Pause';
    pause.setAttribute('aria-label', paused ? 'Play slideshow' : 'Pause slideshow');
  }
  document.querySelector('#hero-prev').addEventListener('click', () => { showSlide(current - 1); schedule(); });
  document.querySelector('#hero-next').addEventListener('click', () => { showSlide(current + 1); schedule(); });
  pause.addEventListener('click', () => { paused = !paused; schedule(); });
  sahara.addEventListener('mouseenter', schedule);
  sahara.addEventListener('mouseleave', schedule);
  sahara.addEventListener('focusin', schedule);
  sahara.addEventListener('focusout', () => setTimeout(schedule, 0));
  document.addEventListener('visibilitychange', schedule);
  let touchX;
  sahara.addEventListener('touchstart', event => { touchX = event.changedTouches[0].clientX; }, {passive: true});
  sahara.addEventListener('touchend', event => {
    if (event.target.closest('input,select,button,a')) return;
    const delta = event.changedTouches[0].clientX - touchX;
    if (Math.abs(delta) > 60) { showSlide(current + (delta < 0 ? 1 : -1)); schedule(); }
  }, {passive: true});
  showSlide(0); schedule();
}
