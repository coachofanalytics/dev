document.addEventListener("DOMContentLoaded", function () {
  const packageCards = document.querySelectorAll(".package-card");
  const continueBtn = document.getElementById("continueBtn");
  const urls = JSON.parse(document.getElementById("payment-urls").textContent);

  let selectedMembership = "";

  packageCards.forEach(card => {
    card.addEventListener("click", () => {
      packageCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");

      selectedMembership = card.getAttribute("data-level") || "";
      updateLink();
    });
  });

  function updateLink() {
    if (selectedMembership) {
      const base = urls["partial"];
      const href = `${base}?purpose=${encodeURIComponent(selectedMembership)}%20Membership`;
      continueBtn.href = href;
      continueBtn.classList.remove("disabled");
      continueBtn.setAttribute("aria-disabled", "false");
    } else {
      continueBtn.href = "#";
      continueBtn.classList.add("disabled");
      continueBtn.setAttribute("aria-disabled", "true");
    }
  }
});