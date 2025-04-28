/*
    Rolsa Technologies
    carbon_footprint.js
*/

let current_type = null;

function show_form(type) {
    current_type = type;
    document.getElementById("individual-form").style.display = type === "individual" ? "block" : "none";
    document.getElementById("commercial-form").style.display = type === "commercial" ? "block" : "none";
    document.getElementById("type-selection").style.display = "none";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("error-message").style.display = "none";

    document.querySelectorAll(".submit-button").forEach(button =>
        button.style.display = "none");
    document.querySelectorAll(".back-button").forEach(button =>
        button.style.display = "none");

    document.querySelector(`#${type}-form .submit-button`).style.display = "block";
    document.querySelector(`#${type}-form .back-button`).style.display = "block";
}

function go_back() {
    document.getElementById("individual-form").style.display = "none";
    document.getElementById("commercial-form").style.display = "none";
    document.getElementById("type-selection").style.display = "block";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("error-message").style.display = "none";

    current_type = null;
}

function calculate_footprint(type) {
    if (!type) return;

    let data = { type: type };
    let all_empty = true;
    let valid = true;

    if (type === "individual") {
        data.transport_miles = document.getElementById("transport_miles").value;
        data.electricity_kwh = document.getElementById("electricity_kwh").value;
        data.meat_meals = document.getElementById("meat_meals").value;

        // Check if all fields are empty
        all_empty = !data.transport_miles && !data.electricity_kwh && !data.meat_meals;
        if (!all_empty) {
            data.transport_miles = parseFloat(data.transport_miles) || 0;
            data.electricity_kwh = parseFloat(data.electricity_kwh) || 0;
            data.meat_meals = parseFloat(data.meat_meals) || 0;
            valid = data.transport_miles >= 0 && data.electricity_kwh >= 0 && data.meat_meals >= 0;
        }
    } else {
        data.electricity_kwh = document.getElementById("electricity_kwh_dom").value;
        data.gas_kwh = document.getElementById("gas_kwh").value;
        data.waste_tonnes = document.getElementById("waste_tonnes").value;

        // Check if all fields are empty
        all_empty = !data.electricity_kwh && !data.gas_kwh && !data.waste_tonnes;
        if (!all_empty) {
            data.electricity_kwh = parseFloat(data.electricity_kwh) || 0;
            data.gas_kwh = parseFloat(data.gas_kwh) || 0;
            data.waste_tonnes = parseFloat(data.waste_tonnes) || 0;
            valid = data.electricity_kwh >= 0 && data.gas_kwh >= 0 && data.waste_tonnes >= 0;
        }
    }

    if (all_empty) {
        document.getElementById("error-message").textContent = "Please enter at least one value";
        document.getElementById("error-message").style.display = "block";
        return;
    }

    if (!valid) {
        document.getElementById("error-message").textContent = "Values cannot be negative";
        document.getElementById("error-message").style.display = "block";
        return;
    }

    fetch("/get-carbon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error); });
        }
        return response.json();
    })
    .then(result => {
        document.getElementById("user-impact").textContent = result.footprint;
        document.getElementById("avg-impact").textContent = result.average;
        document.getElementById("results-section").style.display = "block";
        document.getElementById("error-message").style.display = "none";
    })
    .catch(error => {
        document.getElementById("error-message").textContent = error.message;
        document.getElementById("error-message").style.display = "block";
        console.error("Error:", error);
    });
}

function open_popup() {
    document.getElementById("popup-container").style.display = "flex";
}

function close_popup() {
    document.getElementById("popup-container").style.display = "none";
}