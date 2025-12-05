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
});
