/*
    Rolsa Technologies
    products.js
*/

const popup = document.getElementById("product-popup");
const popup_title = document.getElementById("popup-title");
const popup_desc = document.getElementById("popup-description");
const popup_extra = document.getElementById("popup-extra");
const popup_image = document.getElementById("popup-image");
const close = document.querySelector(".close");
const product_details = document.getElementById("product-details");

let product_data = {};

// Fetch products and generate cards
fetch("/api/products")
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        product_data = data;
        generate_product_cards(data);
        event_listener();
        check_url_for_product();
    })
    .catch(error => console.error("Fetch Error:", error));

function generate_product_cards(products) {
    product_details.innerHTML = "";

    Object.entries(products).forEach(([title, info]) => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.setAttribute("role", "listitem");
        card.innerHTML = `
            <img class="product-image-icon" alt="" 
            src="${info.image || "/static/assets/icons/question.png"}" aria-hidden="true">
            <div class="product-section">
                <b class="prod-title">${title}</b>
                <div class="prod-desc">${info.extra || "No description available"}</div>
                <div class="buttons-container" role="group" aria-label="Product actions">
                    <div class="button-details">
                        <div class="get" role="button" aria-label="Get consultation for ${title}">
                        <b class="detail-text">Get Consultation</b></div>
                        <div class="view" role="button" aria-label="View details for ${title}">
                        <b class="detail-text">View Details</b></div>
                    </div>
                </div>
            </div>
        `;
        product_details.appendChild(card);
    });
}

function event_listener() {
    // Event listener for "View Details" buttons
    document.querySelectorAll(".view").forEach(button => {
        button.addEventListener("click", (event) => {
            const product_card = event.target.closest(".product-card");
            const title = product_card.querySelector(".prod-title").textContent.trim();
            show_popup(title);
        });
    });

    document.querySelectorAll(".get").forEach(button => {
        button.addEventListener("click", (event) => {
            const product_card = event.target.closest(".product-card");
            const title = product_card.querySelector(".prod-title").textContent.trim();
            window.location.href = `/schedule-page?product=${encodeURIComponent(title)}`;
        });
    });

    document.querySelector(".get-consultation").addEventListener("click", () => {
        const title = popup_title.textContent.trim();
        window.location.href = `/schedule-page?product=${encodeURIComponent(title)}`;
    });
}

function show_popup(title) {
    const data = product_data[title];
    popup_title.textContent = title;
    popup_desc.textContent = data?.extra || "No description available";
    popup_extra.textContent = data?.details || "No additional info available";
    popup_image.src = data?.image || "/static/assets/icons/question.png";
    popup.style.display = "flex";
}

function check_url_for_product() {
    const urlParams = new URLSearchParams(window.location.search);
    const product = urlParams.get("product");
    if (product && product_data[product]) {
        show_popup(product);
    }
}

// Close popup
close.addEventListener("click", () => {
    popup.style.display = "none";
});

window.addEventListener("click", (event) => {
    if (event.target === popup) {
        popup.style.display = "none";
    }
});