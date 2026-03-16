const foodGrid = document.getElementById("foodGrid");
const infoBox = document.getElementById("infoBox");
const pdfLinks = document.getElementById("pdfLinks");
const foodPlanHeading = document.getElementById("foodPlanHeading");
const foodHeroTitle = document.getElementById("foodHeroTitle");
const dietPlans = window.dietPlans || {};
const appRoutes = window.appRoutes || {};
const savedDietPlan = localStorage.getItem("selectedDietPlan");
const requestedDietPlan = window.defaultDietPlan || "days-1-14";
const activeDietPlan = savedDietPlan && dietPlans[savedDietPlan] ? savedDietPlan : requestedDietPlan;

function buildDietPdfUrl(planKey) {
    const pattern = appRoutes.downloadDietPdfPattern;
    if (pattern && pattern.includes("__PLAN_KEY__")) {
        return pattern.replace("__PLAN_KEY__", encodeURIComponent(planKey));
    }
    return `/download-diet-pdf/${planKey}`;
}

function renderFoods(planKey) {
    const plan = dietPlans[planKey];
    if (!plan) {
        return;
    }

    infoBox.innerText = `${plan.title}: ${plan.description}`;
    foodGrid.innerHTML = "";

    plan.items.forEach((item) => {
        foodGrid.innerHTML += `
            <div class="food-card">
                <h3>${item.name}</h3>
                <p>${item.desc}</p>
            </div>
        `;
    });
}

function renderPdfLink(planKey) {
    const plan = dietPlans[planKey];
    if (!plan) {
        return;
    }

    if (foodHeroTitle) {
        foodHeroTitle.innerText = `${plan.label} PCOD Food Plan`;
    }

    if (foodPlanHeading) {
        foodPlanHeading.innerText = plan.title;
    }

    pdfLinks.innerHTML = `
        <a class="pdf-link active-pdf" href="${buildDietPdfUrl(planKey)}">
            Download ${plan.label} PDF
        </a>
    `;
}

renderFoods(activeDietPlan);
renderPdfLink(activeDietPlan);
