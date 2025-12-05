// Minimal JS for cookie banner and simple interactions
document.addEventListener('DOMContentLoaded', function(){
  var banner = document.getElementById('cookie-banner');
  if(!banner) return;
  var accept = document.getElementById('cookie-accept');
  var customize = document.getElementById('cookie-customize');
  if(localStorage.getItem('bb_cookies') === 'accepted'){
    banner.style.display = 'none';
  }
  accept.addEventListener('click', function(){
    localStorage.setItem('bb_cookies','accepted');
    banner.style.display = 'none';
  });
  customize.addEventListener('click', function(){
    alert('Cookie settings placeholder — configure as needed.');
  });
  // Initialize Swiper if present
  try {
    if (typeof Swiper !== 'undefined') {
      var swipers = document.querySelectorAll('.swiper, .swiper-container');
      swipers.forEach(function(el) {
        // basic initialization if not already initialized
        if (!el.classList.contains('swiper-initialized')) {
          new Swiper(el, {
            loop: true,
            slidesPerView: 1,
            autoplay: { delay: 5000 },
            pagination: { el: el.querySelector('.swiper-pagination'), clickable: true },
            navigation: {
              nextEl: el.querySelector('.swiper-button-next'),
              prevEl: el.querySelector('.swiper-button-prev')
            }
          });
        }
      });
    }
  } catch(e) {
    console.warn('Swiper init failed', e);
  }

  // Initialize Jarallax if present
  try {
    if (typeof jarallax !== 'undefined') {
      var jar = document.querySelectorAll('.jarallax');
      if (jar.length) jarallax(jar, { speed: 0.5 });
    }
  } catch(e) {
    console.warn('Jarallax init failed', e);
  }
});
