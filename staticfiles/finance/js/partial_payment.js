document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.partial-payment-form'); // or unique container
  if (!root) return;
  
  const presetButtons = document.querySelectorAll('.amount-button');
  const paymentButtons = document.querySelectorAll('.payment-button');

  let selectedAmount = '25';
  const incoming = new URLSearchParams(window.location.search);
  if (!incoming.has('purpose')) incoming.set('purpose', 'donation');

  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedAmount = btn.getAttribute('data-value');
    });
  });

  paymentButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();              // <-- important
      e.stopPropagation();

      const baseUrl = btn.dataset.url; // e.g., /finance/stripe/checkout/
      if (!baseUrl) return;

      const dest = new URL(baseUrl, window.location.origin);
      const params = new URLSearchParams(incoming.toString());

      params.set('partial_amount', selectedAmount);
      params.set('partial_purpose', 'Partial Payment');

      const method = btn.dataset.method || '';
      if (method) params.set('method', method);

      dest.search = params.toString();
      window.location.href = dest.toString();
    });
  });
});
