document.addEventListener("DOMContentLoaded", function () {
  const root = document.querySelector('.payment-container'); // or unique container
  if (!root) return;

  const payNowBtn = document.getElementById("payNowBtn");
  const partialPayBtn = document.getElementById("partialPayBtn");
  const packageCards = document.querySelectorAll(".package-card");
  const paymentOptions = document.querySelectorAll(".icon-button");
  const urls = JSON.parse(document.getElementById("payment-urls").textContent);

  let selectedAmount = "";
  let selectedMethod = "";
  let selectedMembership = "";

  // package selection
  packageCards.forEach(card => {
    card.addEventListener("click", () => {
      packageCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedAmount = card.getAttribute("data-amount") || "";
      selectedMembership = card.getAttribute("lead-level") || "";
      updateLinks();
    });
  });

  // payment method selection
  paymentOptions.forEach(option => {
    option.addEventListener("click", () => {
      paymentOptions.forEach(opt => opt.classList.remove("selected"));
      option.classList.add("selected");
      selectedMethod = option.getAttribute("data-method") || "";
      updateLinks();
    });
  });

  // enable/disable buttons + set hrefs
  function updateLinks() {
    const ready = Boolean(selectedMethod && selectedAmount);

    if (ready) {
      // Full payment link (use chosen method's URL)
      const fullBase = urls[selectedMethod] || "#";
      const fullHref = `${fullBase}?amount=${encodeURIComponent(selectedAmount)}&purpose=${encodeURIComponent(selectedMembership)}%20Membership`;
      activateLink(payNowBtn, fullHref);

      // Partial payment link (go to your partial-payment page)
      // Pass the same context + selected method so that page knows what to do.
      const partialBase = urls["partial"] || "#";
      const partialHref = `${partialBase}?amount=${encodeURIComponent(selectedAmount)}&purpose=${encodeURIComponent(selectedMembership)}%20Membership&method=${encodeURIComponent(selectedMethod)}&mode=partial`;
      activateLink(partialPayBtn, partialHref);
    } else {
      deactivateLink(payNowBtn);
      deactivateLink(partialPayBtn);
    }
  }

  function activateLink(el, href) {
    el.href = href;
    el.classList.remove("disabled");
    el.setAttribute("aria-disabled", "false");
  }

  function deactivateLink(el) {
    el.href = "#";
    el.classList.add("disabled");
    el.setAttribute("aria-disabled", "true");
  }

  // initialize state
  updateLinks();
});
