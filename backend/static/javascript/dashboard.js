const userName = localStorage.getItem("userName");
const userNameEl = document.querySelector(".username");

if (userName && userNameEl) {
    userNameEl.innerText = `Hi, ${userName}`;
}

const tipText = document.getElementById("wellnessTipText");
const tips = [
    "Drink warm water to support digestion.",
    "Sleep at least 7-8 hours for hormone balance.",
    "Avoid excess sugar today.",
    "Do 10 minutes of breathing exercises.",
    "Stay hydrated throughout the day.",
];

if (tipText) {
    const randomTip = tips[Math.floor(Math.random() * tips.length)];
    tipText.innerText = randomTip;
}

const dietPlans = window.dietPlans || {};
const defaultDietPlan = window.defaultDietPlan || "days-1-14";
const dietPlanSelect = document.getElementById("dashboardDietPlan");
const plannerNote = document.getElementById("plannerNote");
const foodCardLink = document.getElementById("foodCardLink");
const foodCardDescription = document.getElementById("foodCardDescription");
const foodPlanLinkText = document.getElementById("foodPlanLinkText");
const dietPdfCardLink = document.getElementById("dietPdfCardLink");
const dietPdfDescription = document.getElementById("dietPdfDescription");
const trackerModal = document.getElementById("trackerModal");
const trackerFirstInput = document.getElementById("trackerAge");
const cycleDayValue = document.getElementById("cycleDayValue");
const cycleDayHint = document.getElementById("cycleDayHint");
const selectedPlanInputs = document.querySelectorAll(".selected-plan-input");
const appRoutes = window.appRoutes || {};

function buildFoodPageUrl(planKey) {
    const foodBase = appRoutes.foodBase || "/food";
    const url = new URL(foodBase, window.location.origin);
    url.searchParams.set("plan", planKey);
    return `${url.pathname}${url.search}`;
}

function buildDietPdfUrl(planKey) {
    const pattern = appRoutes.downloadDietPdfPattern;
    if (pattern && pattern.includes("__PLAN_KEY__")) {
        return pattern.replace("__PLAN_KEY__", encodeURIComponent(planKey));
    }
    return `/download-diet-pdf/${planKey}`;
}

function getPlanDuration(planKey, plan) {
    if (plan && typeof plan.duration_days === "number") {
        return plan.duration_days;
    }

    if (typeof planKey === "string") {
        const keyNumbers = planKey.match(/\d+/g);
        if (keyNumbers && keyNumbers.length > 0) {
            return Math.max(...keyNumbers.map(Number));
        }
    }

    if (plan && typeof plan.label === "string") {
        const labelNumbers = plan.label.match(/\d+/g);
        if (labelNumbers && labelNumbers.length > 0) {
            return Math.max(...labelNumbers.map(Number));
        }
    }

    return 45;
}

function updateCycleDayDisplay(planKey) {
    if (!cycleDayValue) {
        return;
    }

    const cycleDay = Number(cycleDayValue.dataset.cycleDay || 0);
    const selectedPlan = dietPlans[planKey];
    const selectedDuration = getPlanDuration(planKey, selectedPlan);

    if (Number.isNaN(cycleDay) || !selectedDuration) {
        return;
    }

    const displayDay = Math.min(cycleDay, selectedDuration);
    cycleDayValue.innerText = `Day ${displayDay} / ${selectedDuration}`;

    if (!cycleDayHint) {
        return;
    }

    if (cycleDay > selectedDuration) {
        cycleDayHint.innerText = `Cycle day exceeds this plan range. Showing the maximum day for the selected plan.`;
    } else {
        cycleDayHint.innerText = `Tracking for your selected ${selectedDuration}-day plan.`;
    }
}

function updateDietPlanSelection(planKey) {
    const plan = dietPlans[planKey];
    if (!plan) {
        return;
    }

    localStorage.setItem("selectedDietPlan", planKey);

    if (dietPlanSelect) {
        dietPlanSelect.value = planKey;
    }

    if (plannerNote) {
        plannerNote.innerText = `${plan.label}: ${plan.description}`;
    }

    selectedPlanInputs.forEach((input) => {
        input.value = planKey;
    });

    if (foodCardLink) {
        foodCardLink.href = buildFoodPageUrl(planKey);
    }

    if (foodCardDescription) {
        foodCardDescription.innerText = `PCOD-friendly diet guidance for ${plan.label}.`;
    }

    if (foodPlanLinkText) {
        foodPlanLinkText.innerText = `Open ${plan.label} Diet Plan`;
    }

    if (dietPdfCardLink) {
        dietPdfCardLink.href = buildDietPdfUrl(planKey);
    }

    if (dietPdfDescription) {
        dietPdfDescription.innerText = `Download the ${plan.label} diet plan as a PDF.`;
    }

    updateCycleDayDisplay(planKey);
}

if (dietPlanSelect) {
    const savedDietPlan = localStorage.getItem("selectedDietPlan");
    const startingPlan = savedDietPlan && dietPlans[savedDietPlan] ? savedDietPlan : defaultDietPlan;
    updateDietPlanSelection(startingPlan);

    dietPlanSelect.addEventListener("change", (event) => {
        updateDietPlanSelection(event.target.value);
    });
}

if (window.showTrackerPopup && trackerModal && trackerFirstInput) {
    trackerFirstInput.focus();
}
