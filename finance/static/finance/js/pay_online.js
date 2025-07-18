document.addEventListener("DOMContentLoaded", function () {
    const payNowBtn = document.getElementById("payNowBtn");
    const packageCards = document.querySelectorAll('.package-card');
    const paymentOptions = document.querySelectorAll('.icon-button');
    const urls = JSON.parse(document.getElementById("payment-urls").textContent);

    let selectedAmount = "";
    let selectedMethod = "";

    // Handle package card selection
    packageCards.forEach(card => {
        card.addEventListener('click', () => {
        packageCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedAmount = card.getAttribute('data-amount');
        updatePayNowLink();
        });
    });

    // Handle payment method selection
    paymentOptions.forEach(option => {
        option.addEventListener('click', () => {
        paymentOptions.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        selectedMethod = option.getAttribute('data-method');
        updatePayNowLink();
        });
    });

    // Enable Pay Now button if only the user has selected the package and payment method
    function updatePayNowLink() {
      if (selectedMethod && selectedAmount) {
        const baseUrl = urls[selectedMethod];
        const fullUrl = `${baseUrl}?amount=${encodeURIComponent(selectedAmount)}&purpose=general`;
        payNowBtn.href = fullUrl;
        payNowBtn.classList.remove("disabled");
        payNowBtn.setAttribute("aria-disabled", "false");
      } else {
        payNowBtn.href = "#";
        payNowBtn.classList.add("disabled");
        payNowBtn.setAttribute("aria-disabled", "true");
     }
    }
});