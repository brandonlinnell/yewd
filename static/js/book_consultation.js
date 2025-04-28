/*
    Rolsa Technologies
    book_consultation.js
*/

// Dynamically add to the Product Type dropdown and parameter product
document.addEventListener("DOMContentLoaded", async () => {
    const product_dropdown = document.getElementById("product");
    const confirm_button = document.querySelector(".confirm-button");

    try {
        const response = await fetch("/api/products");
        const products = await response.json();

        // Populate dropdown with product options
        Object.entries(products).forEach(([product_type]) => {
            const option = document.createElement("option");
            option.value = product_type;
            option.textContent = product_type;
            product_dropdown.appendChild(option);
        });

        // Check URL for product parameter and select it
        const urlParams = new URLSearchParams(window.location.search);
        const selectedProduct = urlParams.get("product");
        if (selectedProduct) {
            product_dropdown.value = selectedProduct;
        }

        confirm_button.disabled = false;
    } catch (error) {
        console.error("Error fetching products:", error);
        const error_message = document.querySelector(".error-message");
        error_message.textContent = "Error loading products. Please try again later.";
        confirm_button.disabled = true;
    }
});

// Submit consultation to app
document.querySelector(".confirm-button").addEventListener("click", async () => {
    const error_message = document.querySelector(".error-message");
    const success_message = document.querySelector(".success-message");

    // Clear previous messages
    error_message.textContent = "";
    success_message.textContent = "";

    const fullname = document.getElementById("fullname").value;
    const product_type = document.getElementById("product").value;
    const property_type = document.getElementById("property").value;
    const postcode = document.getElementById("postcode").value;
    const preferred_date = document.getElementById("date").value;

    // Check if fields are empty
    if (!fullname || !product_type || !property_type || !postcode || !preferred_date) {
        error_message.textContent = "Please fill in all fields before submitting the consultation";
        return;
    }

    // Ensure full name contains only letters and spaces
    const name_pattern = /^[A-Za-z\s]+$/;
    if (!name_pattern.test(fullname)) {
        error_message.textContent = "Full name must contain only letters and spaces, no numbers";
        return;
    }

    // Ensure full_name is not just spaces
    if (fullname.trim().length === 0 || !/[A-Za-z]/.test(fullname)) {
        error_message.textContent = "Full name must contain at least one letter, not just spaces";
        return;
    }

    // Ensure postcode is 8 characters or less
    if (postcode.length > 8) {
        error_message.textContent = "Postcode must be 8 characters or less";
        return;
    }

    // Ensure preferred_date is after today
    const today = new Date();
    const selected_date = new Date(preferred_date);
    if (selected_date <= today) {
        error_message.textContent = "Preferred date must be after today";
        return;
    }

    const consultation_data = {
        full_name: fullname,
        product_type: product_type,
        property_type: property_type,
        postcode: postcode,
        preferred_date: preferred_date,
    };

    // Submit POST request
    try {
        const response = await fetch("/submit-consultation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(consultation_data)
        });

        const result = await response.json();

        if (result.success) {
            success_message.textContent = "Consultation submitted successfully";
            // Redirect to dashboard if redirect URL is provided
            if (result.redirect) {
                window.location.href = result.redirect;
            }
        } else {
            error_message.textContent = result.error || "Failed to submit consultation";
        }
    } catch (error) {
        console.error("Error submitting consultation:", error);
        error_message.textContent = "Failed to submit consultation. Please try again.";
    }
});