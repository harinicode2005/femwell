const lastPeriod = localStorage.getItem("lastPeriodDate");
const seedGrid = document.getElementById("seedGrid");
const phaseTitle = document.getElementById("phaseTitle");
const warningBox = document.getElementById("warningBox");

function addSeed(name, img, desc) {
    seedGrid.innerHTML += `
        <div class="seed-card">
            <img src="${img}" alt="${name}">
            <h3>${name}</h3>
            <p>${desc}</p>
        </div>
    `;
}

if (!lastPeriod) {
    phaseTitle.innerText = "Cycle data not available";
} else {
    const lastDate = new Date(lastPeriod);
    const today = new Date();
    const dayCount = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));

    if (dayCount >= 1 && dayCount <= 14) {
        phaseTitle.innerText = "Follicular Phase (Day 1-14)";
        addSeed("Flax Seeds", "/static/images/flax.jpg", "Supports estrogen balance");
        addSeed("Pumpkin Seeds", "/static/images/pumpkin.jpg", "Rich in zinc for ovulation");
    } else if (dayCount >= 15 && dayCount <= 45) {
        phaseTitle.innerText = "Luteal Phase (Day 15-45)";
        addSeed("Sunflower Seeds", "/static/images/sunflower.jpg", "Supports progesterone");
        addSeed("Sesame Seeds", "/static/images/sesame.jpg", "Improves hormonal balance");
    } else {
        phaseTitle.innerText = "Extended Cycle (PCOD Care)";
        warningBox.classList.remove("hidden");
        addSeed("Sunflower Seeds", "/static/images/sunflower.jpg", "Hormone regulation");
        addSeed("Sesame Seeds", "/static/images/sesame.jpg", "Supports cycle balance");
    }
}
