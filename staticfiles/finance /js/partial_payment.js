// finance/static/finance/js/partial_payment.js
document.addEventListener("DOMContentLoaded", function () {
  const amountButtons = document.querySelectorAll(".amount-btn");
  const methodButtons = document.querySelectorAll(".method-btn");
  const proceedBtn = document.getElementById("proceed-btn");

  // Data from server/context
  const purpose = document.getElementById("pp-purpose")?.value || "";
  const totalAmount = parseFloat(document.getElementById("pp-total")?.value || "0");
  const balance = parseFloat(document.getElementById("pp-balance")?.value || "0");

  let selectedAmount = null;
  let selectedMethod = null;

  // Select amount
  amountButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      // Check if balance is already cleared
      if (balance <= 0) {
        alert("You have already cleared your balance. No further payments are required.");
        selectedAmount = null;
        amountButtons.forEach(b => b.classList.remove("selected"));
        toggleProceed();
        return; // stop further logic
      }

      // Reset and mark selected
      amountButtons.forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedAmount = parseFloat(btn.dataset.amount);

      // Enforce balance cap
      if (balance > 0 && selectedAmount > balance) {
        alert(`Your remaining balance is $${balance.toFixed(2)}. Please select $${balance.toFixed(0)} or less.`);
        // Deselect and reset
        btn.classList.remove("selected");
        selectedAmount = null;
      }

      toggleProceed();
    });
  });

  // Select payment method
  methodButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      methodButtons.forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedMethod = btn.dataset.method;
      toggleProceed();
    });
  });

  // Enable/disable proceed
  function toggleProceed() {
    proceedBtn.disabled = !(selectedAmount && selectedMethod);
  }

  // Proceed
  proceedBtn.addEventListener("click", () => {
    if (!selectedAmount || !selectedMethod) return;

    // Build a method-specific URL. Adjust to your URL names/routes.
    // Examples:
    //   /finance/pay/card/?amount=50&purpose=...&total_amount=...
    //   /finance/pay/paypal/?amount=25&purpose=...&total_amount=...
    //   /finance/pay/zelle/?amount=100&purpose=...&total_amount=...
    const base = `/finance/${encodeURIComponent(selectedMethod)}/checkout/`;
    const qs = new URLSearchParams({
      amount: selectedAmount.toString(),
      purpose: purpose,
      total_amount: totalAmount.toString()
    }).toString();

    window.location.href = `${base}?${qs}`;
  });
});
