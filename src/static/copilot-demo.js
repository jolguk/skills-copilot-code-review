document.addEventListener("DOMContentLoaded", () => {
  const projectWindow = document.querySelector(".project-window");
  const goalForm = document.getElementById("goal-form");
  const goalInput = document.getElementById("project-goal");
  const projectResult = document.getElementById("project-result");
  const addContext = document.getElementById("add-context");
  const contextFeedback = document.getElementById("context-feedback");
  const automationButton = document.getElementById("automation-button");
  const automationFeedback = document.getElementById("automation-feedback");
  const desktopButton = document.getElementById("desktop-button");
  const desktopFeedback = document.getElementById("desktop-feedback");
  const stepLinks = [...document.querySelectorAll(".step-link")];

  goalForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const goal = goalInput.value.trim();
    if (!goal) {
      goalInput.setCustomValidity("Describe a goal to start the sample project.");
      goalInput.reportValidity();
      return;
    }

    goalInput.setCustomValidity("");
    projectWindow.classList.add("is-running");
    projectWindow.querySelector(".window-status").innerHTML = '<span class="live-dot"></span> Coordinating';
    projectResult.querySelector(".result-badge").textContent = "SAMPLE PROJECT STARTED";
    projectResult.querySelectorAll(".agent-state").forEach((state, index) => {
      state.textContent = index === 0 ? "Working" : index === 1 ? "Queued" : "Review";
    });
  });

  goalInput.addEventListener("input", () => goalInput.setCustomValidity(""));

  addContext.addEventListener("click", () => {
    const chips = goalForm.querySelector(".project-context");
    if (!chips.querySelector('[data-extra-context="true"]')) {
      const chip = document.createElement("span");
      chip.className = "context-chip";
      chip.dataset.extraContext = "true";
      chip.textContent = "Launch brief";
      chips.insertBefore(chip, addContext);
    }
    contextFeedback.textContent = "Launch brief added to this sample project.";
  });

  document.querySelectorAll(".connect-button").forEach((button) => {
    button.addEventListener("click", () => {
      const added = button.getAttribute("aria-pressed") !== "true";
      button.setAttribute("aria-pressed", String(added));
      button.classList.toggle("is-connected", added);
      button.textContent = added ? "Added" : "Add";
      const toolName = button.closest(".tool-row").querySelector(".tool-name strong").textContent;
      contextFeedback.textContent = added
        ? `${toolName} added to this sample project.`
        : `${toolName} removed from this sample project.`;
    });
  });

  automationButton.addEventListener("click", () => {
    automationFeedback.textContent = "Sample rule: when a feature lands, prepare a promo video for review.";
    automationButton.textContent = "Automation previewed";
  });

  desktopButton.addEventListener("click", () => {
    desktopFeedback.textContent = "Sample handoff complete: design reviewed → browser preview prepared → ready for your review.";
    desktopButton.textContent = "Sample complete";
  });

  const sections = stepLinks
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((first, second) => second.intersectionRatio - first.intersectionRatio)[0];
      if (!visible) return;

      stepLinks.forEach((link) => {
        const active = link.getAttribute("href") === `#${visible.target.id}`;
        link.classList.toggle("is-active", active);
        if (active) link.setAttribute("aria-current", "step");
        else link.removeAttribute("aria-current");
      });
    }, { rootMargin: "-15% 0px -65% 0px", threshold: [0, 0.25, 0.5] });

    sections.forEach((section) => observer.observe(section));
  }
});
