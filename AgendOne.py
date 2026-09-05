<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gallery con Anteprima Ingrandita</title>
  <style>
    :root {
      --primary-color: #2563eb;
      --bg-overlay: rgba(15, 23, 42, 0.75);
      --card-bg: #ffffff;
      --text-main: #1e293b;
      --text-muted: #64748b;
    }

    body {
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: #f8fafc;
      margin: 0;
    }

    /* Container Galleria */
    .carousel-container {
      position: relative;
      width: 100%;
      max-width: 800px;
      margin: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Immagine Principale */
    .main-image-wrapper {
      position: relative;
      width: 100%;
      height: 450px;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }

    .main-image {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s ease;
    }

    /* Pulsanti Frecce Moderni */
    .nav-btn {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 10;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .nav-btn:hover {
      background: #ffffff;
      transform: translateY(-50%) scale(1.1);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      color: var(--primary-color);
    }

    .nav-btn-prev { left: 16px; }
    .nav-btn-next { right: 16px; }

    .nav-btn svg {
      width: 24px;
      height: 24px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    /* Banner/Popup Anteprima Ingrandito */
    .preview-banner {
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      width: 85%;
      max-width: 600px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      padding: 20px 24px;
      border-radius: 14px;
      box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.25);
      border: 1px solid rgba(255, 255, 255, 0.8);
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 20;
    }

    /* Mostra banner al passaggio del mouse sul container o sulle frecce */
    .carousel-container:hover .preview-banner,
    .nav-btn:hover ~ .preview-banner {
      opacity: 1;
      visibility: visible;
      transform: translateX(-50%) translateY(0);
    }

    .preview-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0 0 8px 0;
      line-height: 1.3;
    }

    .preview-description {
      font-size: 1rem;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.5;
    }
  </style>
</head>
<body>

  <div class="carousel-container">
    <!-- Pulsante Sinistra -->
    <button class="nav-btn nav-btn-prev" onclick="changeSlide(-1)" aria-label="Precedente">
      <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
    </button>

    <!-- Immagine Principale -->
    <div class="main-image-wrapper">
      <img id="current-img" class="main-image" src="https://picsum.photos/id/1018/800/450" alt="Galleria">
    </div>

    <!-- Pulsante Destra -->
    <button class="nav-btn nav-btn-next" onclick="changeSlide(1)" aria-label="Successivo">
      <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>
    </button>

    <!-- Banner Ingrandito -->
    <div class="preview-banner" id="preview-banner">
      <h3 class="preview-title" id="banner-title">Montagne al Tramonto</h3>
      <p class="preview-description" id="banner-desc">Una vista panoramica sulle cime alpine illuminate dagli ultimi raggi di sole della sera.</p>
    </div>
  </div>

  <script>
    const slides = [
      {
        url: "https://picsum.photos/id/1018/800/450",
        title: "Montagne al Tramonto",
        desc: "Una vista panoramica sulle cime alpine illuminate dagli ultimi raggi di sole della sera."
      },
      {
        url: "https://picsum.photos/id/1015/800/450",
        title: "Valle con Fiume",
        desc: "Un fiume limpido che scorre attraverso una vallata rigogliosa immersa nella natura incontaminata."
      },
      {
        url: "https://picsum.photos/id/1019/800/450",
        title: "Costa e Oceano",
        desc: "Onde dell'oceano che si infrangono sulle scogliere rocciose lungo la linea costiera."
      }
    ];

    let currentIndex = 0;

    function updateSlide() {
      const imgEl = document.getElementById('current-img');
      const titleEl = document.getElementById('banner-title');
      const descEl = document.getElementById('banner-desc');

      imgEl.src = slides[currentIndex].url;
      titleEl.textContent = slides[currentIndex].title;
      descEl.textContent = slides[currentIndex].desc;
    }

    function changeSlide(direction) {
      currentIndex = (currentIndex + direction + slides.length) % slides.length;
      updateSlide();
    }
  </script>

</body>
</html>
