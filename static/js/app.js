const menu = document.querySelector(".menu-toggle");
const navLinks = document.querySelector("#nav-links");

if (menu && navLinks) {
  menu.addEventListener("click", () => {
    const open = menu.getAttribute("aria-expanded") !== "true";
    menu.setAttribute("aria-expanded", String(open));
    navLinks.classList.toggle("open", open);
  });
}

const homeHero = document.querySelector(".home-hero");
const heroSlides = homeHero ? homeHero.querySelector(".hero-slides") : null;

if (homeHero && heroSlides) {
  const slideImages = [
    "/static/images/hero-island.jpg",
    "/static/images/hero-caribbean.jpg",
    "/static/images/hero-kenya.jpg"
  ];

  slideImages.forEach((image, index) => {
    const slide = document.createElement("div");
    slide.className = "hero-slide";
    if (index === 0) {
      slide.classList.add("active");
    }
    slide.style.backgroundImage = `linear-gradient(180deg,#e8b78d66,#824a2340), url("${image}")`;
    heroSlides.append(slide);
  });

  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches && slideImages.length > 1) {
    const slides = heroSlides.querySelectorAll(".hero-slide");
    let current = 0;
    window.setInterval(() => {
      slides[current].classList.remove("active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("active");
    }, 5000);
  }
}
