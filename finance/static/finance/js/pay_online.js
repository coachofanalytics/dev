// finance/static/finance/js/pay_online.js
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".package-card");
  const continueBtn = document.getElementById("continueBtn"); // or your existing button
  const urls = JSON.parse(document.getElementById("payment-urls").textContent); 
  // Make sure you have: { "partial": "{% url 'finance:partial_payment' %}" } in the JSON

  let selectedMembership = "";
  let selectedPrice = "";

  cards.forEach(card => {
    card.addEventListener("click", () => {
      cards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");

      selectedMembership = card.getAttribute("lead-level") || "";
      // even if you don’t display the price, keep it in the DOM as data-amount
      selectedPrice = card.getAttribute("data-amount") || "";

      updateLink();
    });
  });

  function updateLink() {
    if (!selectedMembership || !selectedPrice) {
      if (continueBtn) {
        continueBtn.href = "#";
        continueBtn.classList.add("disabled");
        continueBtn.setAttribute("aria-disabled", "true");
      }
      return;
    }

    const base = urls["partial"]; // e.g. /finance/partial-payment/
    const href = `${base}?purpose=${encodeURIComponent(selectedMembership)}%20Membership&total_amount=${encodeURIComponent(selectedPrice)}`;

    if (continueBtn) {
      continueBtn.href = href;
      continueBtn.classList.remove("disabled");
      continueBtn.setAttribute("aria-disabled", "false");
    }
  }
});
