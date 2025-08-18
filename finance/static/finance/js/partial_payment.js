document.addEventListener("DOMContentLoaded", function () {
  const amountButtons = document.querySelectorAll(".amount-btn");
  const methodButtons = document.querySelectorAll(".method-btn");
  const proceedBtn = document.getElementById("proceed-btn");

  let selectedAmount = null;
  let selectedMethod = null;

  // Select amount
  amountButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      amountButtons.forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedAmount = btn.dataset.amount;
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

  // Handle proceed
  proceedBtn.addEventListener("click", () => {
    if (!selectedAmount || !selectedMethod) return;

    if (selectedMethod === "stripe") {
      window.location.href = `/finance/stripe/checkout/?amount=${selectedAmount}`;
    } else if (selectedMethod === "zelle") {
      window.location.href = `/finance/zelle/instructions/?amount=${selectedAmount}`;
    } else if (selectedMethod === "paypal") {
      window.location.href = `/finance/paypal/checkout/?amount=${selectedAmount}`;
    }
  });
});
