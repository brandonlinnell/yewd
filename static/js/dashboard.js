/*
    Rolsa Technologies
    dashboard.js
*/

let energy_chart = null;

function close_popup() {
    const popup = document.getElementById("popup-container");
    const form = popup.querySelector("#schedule-form");
    // Clone and replace to clear form inputs
    form.replaceWith(form.cloneNode(true));
    popup.style.display = "none";
}

function close_energy_popup() {
    const popup = document.getElementById("energy-popup-container");
    popup.style.display = "none";
    if (energy_chart) {
        energy_chart.destroy();
        energy_chart = null;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Fetches daily energy usage and updates the interface
    function fetch_daily_usage() {
        fetch("/api/energy-usage", {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        })
            .then((res) => res.json())
            .then((data) => {
                const daily_usage_elem = document.getElementById("tab-daily-usage");
                if (data.success) {
                    daily_usage_elem.textContent = `${data.daily_usage} kWh`;
                } else {
                    console.error("Couldn't get energy data:", data.error);
                    daily_usage_elem.textContent = "N/A";
                }
            })
            .catch((err) => {
                console.error("Error hitting energy API:", err);
                document.getElementById("tab-daily-usage").textContent = "N/A";
            });
    }

    // Run this when the page loads
    fetch_daily_usage();

    // Highlight a consultation row when clicked from activity
    document.querySelectorAll(".consultation-link").forEach((link) => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const consultation_id = link.dataset.consultationId;
            const row = document.querySelector(`tr[data-consultation-id="${consultation_id}"]`);

            if (row) {
                row.scrollIntoView({ behavior: "smooth" });
                row.querySelectorAll("td").forEach((cell) => {
                    cell.classList.add("highlight");
                    // Remove highlight after a couple seconds
                    setTimeout(() => cell.classList.remove("highlight"), 2000);
                });
            }
        });
    });

    // Handle consultation cancellations
    document.querySelectorAll(".cancel-button").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const consultation_id = btn.dataset.consultationId;

            fetch("/cancel-consultation", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: `consultation_id=${consultation_id}`,
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.success) {
                        // Refresh to show updated activity
                        window.location.reload();
                    } else {
                        console.error("Cancellation failed:", data.error);
                        alert("Couldn't cancel the consultation: " + data.error);
                    }
                })
                .catch((err) => {
                    console.error("Error during cancellation:", err);
                    alert("Something went wrong while canceling");
                });
        });
    });

    // Open schedule popup for service/installation
    function show_schedule(consultation_id, service_type) {
        const popup = document.getElementById("popup-container");
        const title = popup.querySelector(".popup-title");
        const form = popup.querySelector("#schedule-form");
        const select_consult = document.getElementById("consultation");
        const date_input = document.getElementById("date");
        const service_input = document.getElementById("service_type");
        const success_message = popup.querySelector(".success-message");
        const error_message = popup.querySelector(".error-message");

        // Clear messages and reset form
        success_message.textContent = "";
        error_message.textContent = "";
        form.reset();

        // Set minimum date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        date_input.min = tomorrow.toISOString().split("T")[0];

        // Update title based on service type
        title.textContent =
            service_type === "maintenance" ? "Schedule Maintenance" : "Schedule Installation";
        service_input.value = service_type;

        // Populate consultation dropdown
        fetch("/api/consultations")
            .then((res) => {
                if (!res.ok) throw new Error("API error: " + res.status);
                return res.json();
            })
            .then((data) => {
                select_consult.innerHTML = '<option value="" disabled selected>Pick a consultation</option>';

                if (!data.success || data.consultations.length === 0) {
                    error_message.textContent = "No consultations available";
                    select_consult.disabled = true;
                } else {
                    data.consultations.forEach((consult) => {
                        const date_section = consult.date_scheduled.split("-");
                        const date_formatted = `${date_section[2]}/${date_section[1]}/${date_section[0]}`;
                        const status = consult.status.charAt(0).toUpperCase() + consult.status.slice(1);
                        const text = `${consult.product_type} - ${date_formatted} (${status})`;
                        const option = document.createElement("option");
                        option.value = consult.id;
                        option.textContent = text.length > 30 ? text.slice(0, 27) + "..." : text;

                        if (consultation_id && consult.id === parseInt(consultation_id)) {
                            option.selected = true;
                        }
                        select_consult.appendChild(option);
                    });
                    select_consult.disabled = false;
                }
            })
            .catch((err) => {
                console.error("Failed to load consultations:", err);
                error_message.textContent = "Error loading consultations";
                select_consult.disabled = true;
            });

        popup.style.display = "flex";

        // Handle form submission
        form.onsubmit = (e) => {
            e.preventDefault();
            success_message.textContent = "";
            error_message.textContent = "";

            if (!select_consult.value) {
                error_message.textContent = "Select a consultation";
                return;
            }
            if (!date_input.value) {
                error_message.textContent = "Pick a date";
                return;
            }
            const selectedDate = new Date(date_input.value);
            if (selectedDate <= new Date()) {
                error_message.textContent = "Date must be in the future";
                return;
            }

            const form_data = new FormData(form);
            fetch("/schedule-request", {
                method: "POST",
                body: form_data,
            })
                .then((res) => {
                    if (!res.ok) throw new Error("Schedule API failed: " + res.status);
                    return res.json();
                })
                .then((data) => {
                    if (data.success) {
                        success_message.textContent = "Scheduled successfully!";
                        setTimeout(() => {
                            close_popup();
                            window.location.reload();
                        }, 1500);
                    } else {
                        error_message.textContent = data.error || "Scheduling failed";
                    }
                })
                .catch((err) => {
                    console.error("Scheduling error:", err);
                    error_message.textContent = "Error while scheduling";
                });
        };
    }

    // Handle schedule service buttons
    document.querySelectorAll(".schedule-service-button, .consultation-button.maintenance")
        .forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                const consultation_id = btn.dataset.consultationId || null;
                const service_type = btn.dataset.serviceType || "maintenance";
                const status = consultation_id
                    ? btn.closest("tr").querySelector(".status").textContent.trim().toLowerCase()
                    : null;

                if (service_type === "installation" && status !== "approved") {
                    const popup = document.getElementById("popup-container");
                    popup.querySelector(".error-message").textContent =
                        "Only approved consultations can be scheduled for installation";
                    popup.style.display = "flex";
                } else {
                    show_schedule(consultation_id, service_type);
                }
            });
        });

    // Open energy usage popup
    function show_energy_popup() {
        const popup = document.getElementById("energy-popup-container");
        popup.style.display = "flex";

        fetch("/api/energy-usage")
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    document.getElementById("daily-usage").textContent = `${data.daily_usage} kWh`;
                    document.getElementById("weekly-usage").textContent = `${data.weekly_usage} kWh`;
                    document.getElementById("monthly-usage").textContent = `${data.monthly_usage} kWh`;
                    document.getElementById("avg-daily-usage").textContent = `${data.avg_daily_usage} kWh`;

                    if (energy_chart) energy_chart.destroy();

                    const ctx = document.getElementById("energy-usage-chart").getContext("2d");
                    energy_chart = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: data.graph_data.labels,
                            datasets: [
                                {
                                    label: "Your Usage",
                                    data: data.graph_data.user_values,
                                    borderColor: "#006837",
                                    fill: false,
                                    tension: 0.3,
                                },
                                {
                                    label: "UK Average",
                                    data: data.graph_data.national_average,
                                    borderColor: "#8bc349",
                                    fill: false,
                                    tension: 0.3,
                                },
                            ],
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true, title: { display: true, text: "kWh" } },
                                x: { title: { display: true, text: "Date" } },
                            },
                            plugins: {
                                legend: { position: "top" },
                                tooltip: {
                                    callbacks: {
                                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} kWh`,
                                    },
                                },
                            },
                        },
                    });
                }
            })
            .catch((err) => console.error("Energy data fetch failed:", err));
    }

    // Attach energy tracking button
    document.querySelector(".track-button").addEventListener("click", (e) => {
        e.preventDefault();
        show_energy_popup();
    });
});