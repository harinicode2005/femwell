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
const assistantForm = document.getElementById("assistantForm");
const assistantInput = document.getElementById("assistantInput");
const assistantMessages = document.getElementById("assistantMessages");
const assistantStatus = document.getElementById("assistantStatus");
const voiceAssistButton = document.getElementById("voiceAssistButton");
const assistantToggleButton = document.getElementById("assistantToggleButton");
const assistantPanel = document.getElementById("assistantPanel");
const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;
let assistantOpen = false;

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

function setAssistantOpenState(nextOpen) {
    if (!assistantPanel || !assistantToggleButton) {
        return;
    }

    assistantOpen = nextOpen;
    assistantPanel.classList.toggle("assistant-panel-hidden", !nextOpen);
    assistantToggleButton.setAttribute("aria-expanded", String(nextOpen));
    assistantToggleButton.textContent = nextOpen ? "Close Assistant" : "Assistant";

    if (nextOpen && assistantInput) {
        window.setTimeout(() => assistantInput.focus(), 120);
    }
}

if (assistantToggleButton && assistantPanel) {
    assistantToggleButton.addEventListener("click", () => {
        setAssistantOpenState(!assistantOpen);
    });
}

function appendAssistantMessage(role, text) {
    if (!assistantMessages) {
        return;
    }

    const message = document.createElement("div");
    message.className = `assistant-message ${role === "user" ? "assistant-message-user" : "assistant-message-bot"}`;
    message.textContent = text;
    assistantMessages.appendChild(message);
    assistantMessages.scrollTop = assistantMessages.scrollHeight;
}

function speakAssistantReply(text) {
    if (!("speechSynthesis" in window) || !text) {
        return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
}

async function sendAssistantMessage(messageText, { speakReply = false } = {}) {
    if (!messageText || !assistantInput) {
        return;
    }

    appendAssistantMessage("user", messageText);
    assistantInput.value = "";

    if (assistantStatus) {
        assistantStatus.textContent = "FemWell Assistant is thinking...";
    }

    try {
        const formData = new FormData();
        formData.append("message", messageText);

        const response = await fetch(appRoutes.assistantQuery || "/assistant/query", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Assistant request failed.");
        }

        const data = await response.json();
        const reply = data.reply || "I could not generate a reply right now.";
        appendAssistantMessage("bot", reply);

        if (assistantStatus) {
            assistantStatus.textContent = "Assistant reply ready.";
        }

        if (speakReply) {
            speakAssistantReply(reply);
        }
    } catch (error) {
        const fallback = "I could not respond right now. Please try again.";
        appendAssistantMessage("bot", fallback);
        if (assistantStatus) {
            assistantStatus.textContent = fallback;
        }
    }
}

if (assistantForm && assistantInput) {
    assistantForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const messageText = assistantInput.value.trim();
        if (!messageText) {
            return;
        }
        await sendAssistantMessage(messageText);
    });
}

if (voiceAssistButton) {
    if (!SpeechRecognitionApi) {
        voiceAssistButton.disabled = true;
        if (assistantStatus) {
            assistantStatus.textContent = "Voice input is not supported in this browser. You can still chat by typing.";
        }
    } else {
        recognition = new SpeechRecognitionApi();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isListening = true;
            voiceAssistButton.textContent = "Listening...";
            if (assistantStatus) {
                assistantStatus.textContent = "Listening. Speak your question now.";
            }
        };

        recognition.onend = () => {
            isListening = false;
            voiceAssistButton.textContent = "Start Voice";
        };

        recognition.onerror = () => {
            if (assistantStatus) {
                assistantStatus.textContent = "Voice input did not work. Please try again or type your question.";
            }
        };

        recognition.onresult = async (event) => {
            const transcript = event.results?.[0]?.[0]?.transcript?.trim() || "";
            if (!transcript) {
                return;
            }
            if (assistantInput) {
                assistantInput.value = transcript;
            }
            await sendAssistantMessage(transcript, { speakReply: true });
        };

        voiceAssistButton.addEventListener("click", () => {
            if (!recognition) {
                return;
            }

            if (isListening) {
                recognition.stop();
                return;
            }

            recognition.start();
        });
    }
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && assistantOpen) {
        setAssistantOpenState(false);
    }
});
