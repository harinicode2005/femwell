const periodForm = document.getElementById("periodForm");

if (periodForm) {
    periodForm.addEventListener("submit", () => {
        const selectedDate = periodForm.querySelector("input[name='last_period_date']");
        if (selectedDate && selectedDate.value) {
            localStorage.setItem("lastPeriodDate", selectedDate.value);
        }
    });
}
