document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.donation-form');
  if (!root) return; // not on donation page, skip

  const presetButtons = document.querySelectorAll('.amount-button');
  const customInput   = document.getElementById('custom_input');
  const paymentButtons = document.querySelectorAll('.payment-button');

  // Default: first preset selected
  let selectedAmount = '25';
  let usingCustom = false;

  // Helpers
  const sanitizeAmount = (raw) => {
    if (!raw) return '';
    // remove $, commas, spaces
    const cleaned = String(raw).replace(/[\$,]/g, '').trim();
    // allow numbers with optional decimal part
    const num = Number(cleaned);
    if (!isFinite(num) || num <= 0) return '';
    // keep as plain string (no formatting) to pass to backend
    return cleaned;
  };

  const clearCustomIfPreset = () => {
    if (customInput) customInput.value = '';
    usingCustom = false;
  };

  const clearPresetsIfCustom = () => {
    presetButtons.forEach(b => b.classList.remove('selected'));
    usingCustom = true;
  };

  // Preset amount selection
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedAmount = btn.innerText.replace('$', '').trim();
      clearCustomIfPreset();
    });
  });

  // Custom typing: once user types a valid positive number, we use it
  if (customInput) {
    customInput.addEventListener('input', () => {
      const cleaned = sanitizeAmount(customInput.value);
      // switch control to custom as soon as user types anything
      clearPresetsIfCustom();
      selectedAmount = cleaned || ''; // empty means invalid/zero
    });

    // Submit on Enter
    customInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        // trigger Stripe if present
        const stripeBtn = document.querySelector('.payment-button[data-method="stripe"]');
        if (stripeBtn) stripeBtn.click();
      }
    });
  }

  // Payment method click
  paymentButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();

      const baseUrl = btn.dataset.url;
      const method  = btn.dataset.method || 'stripe';
      if (!baseUrl || baseUrl === '#') {
        console.warn('Payment URL is missing for', method);
        return;
      }

      // Determine final amount
      let finalAmount = selectedAmount;
      // If using custom, make sure it’s valid right now
      if (usingCustom) {
        finalAmount = sanitizeAmount(customInput.value);
      }

      if (!finalAmount) {
        alert('Please enter or select a valid donation amount.');
        if (customInput && usingCustom) customInput.focus();
        return;
      }

      // Build destination URL
      const dest = new URL(baseUrl, window.location.origin);
      const params = new URLSearchParams();
      params.set('purpose', 'donation');
      params.set('amount', finalAmount);   // dollars as string
      params.set('method', method);        // optional helper
      params.set('source', 'donation');    // helpful for debugging/analytics

      dest.search = params.toString();

      // Debug log (remove if not needed)
      console.log('Redirecting to:', dest.toString());

      window.location.href = dest.toString();
    });
  });
});
