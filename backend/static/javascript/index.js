const featureCards = document.querySelectorAll(".feature-gated");
const signinModal = document.getElementById("signinModal");
const detailsModal = document.getElementById("detailsModal");
const signinForm = document.getElementById("signinModalForm");
const detailsForm = document.getElementById("detailsModalForm");
const signinError = document.getElementById("signinError");
const detailsError = document.getElementById("detailsError");
const closeButtons = document.querySelectorAll("[data-close-modal]");
const appRoutes = window.appRoutes || {};

function openModal(modal) {
    if (!modal) return;
    modal.hidden = false;
    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
    modal.hidden = true;
}

featureCards.forEach((card) => {
    card.addEventListener("click", () => {
        signinError.textContent = "";
        openModal(signinModal);
    });

    card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            signinError.textContent = "";
            openModal(signinModal);
        }
    });
});

closeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        closeModal(signinModal);
        closeModal(detailsModal);
    });
});

[signinModal, detailsModal].forEach((modal) => {
    if (!modal) return;
    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal(modal);
        }
    });
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeModal(signinModal);
        closeModal(detailsModal);
    }
});

if (signinForm) {
    signinForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        signinError.textContent = "";

        const formData = new FormData(signinForm);

        try {
            const response = await fetch(appRoutes.signin || "/signin", {
                method: "POST",
                body: formData,
            });
            const finalUrl = response.url || "";

            if (response.ok && finalUrl.includes("/dashboard")) {
                closeModal(signinModal);
                openModal(detailsModal);
                return;
            }

            signinError.textContent = "Invalid credentials. Please try again.";
        } catch (error) {
            signinError.textContent = "Could not sign in. Please try again.";
        }
    });
}

if (detailsForm) {
    detailsForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        detailsError.textContent = "";

        const formData = new FormData(detailsForm);

        try {
            const response = await fetch(appRoutes.details || "/details", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                detailsError.textContent = "Could not save health details.";
                return;
            }

            window.location.href = appRoutes.dashboard || "/dashboard";
        } catch (error) {
            detailsError.textContent = "Could not save health details.";
        }
    });
}
