document.addEventListener('DOMContentLoaded', function () {
  const presetButtons = document.querySelectorAll('.amount-button');
  const customInput = document.getElementById('custom_input');
  const paymentButtons = document.querySelectorAll('.payment-button');

  let selectedAmount = 25;

  // Preset amount selection
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedAmount = btn.innerText.replace('$', '').trim();
    });
  });

  // Payment method click
  paymentButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const customVal = customInput.value.trim();
      const amount = customVal !== '' ? customVal : selectedAmount;
      const purpose = "donation"

      const baseUrl = btn.dataset.url;  // this comes from Django
      const fullUrl = `${baseUrl}?amount=${amount}&purpose=${purpose}`;
 

      window.location.href = fullUrl;
    });
  });
});
