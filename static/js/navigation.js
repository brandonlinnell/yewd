/*
    Rolsa Technologies
    navigation.js
*/

const products_button = document.querySelector(".products");
const products_bar = document.querySelector(".our-products");

products_button.addEventListener("mouseenter", () => {
    products_bar.style.display = "flex";
    products_button.setAttribute("aria-expanded", "true");
});
products_button.addEventListener("mouseleave", () => {
    setTimeout(() => {
        if (!products_bar.matches(":hover")) {
            products_bar.style.display = "none";
            products_button.setAttribute("aria-expanded", "false");
        }
    }, 200);
});
products_bar.addEventListener("mouseleave", () => {
    products_bar.style.display = "none";
    products_button.setAttribute("aria-expanded", "false");
});

// Trigger accessibility panel via custom button
document.addEventListener("DOMContentLoaded", () => {
    const accessibility_button = document.querySelector(".accessibility-button");
    accessibility_button.addEventListener("click", () => {
        const widget_button = document.querySelector(".asw-menu-btn");
        if (widget_button) {
            widget_button.click();
        }
    });

    const remove_default = () => {
        const widget_button = document.querySelector(".asw-menu-btn");
        if (widget_button) {
            widget_button.style.display = "none";
        } else {
            setTimeout(remove_default, 1);
        }
    };
    remove_default();

    // Hide default button and apply custom styles
    const styles = () => {
        const header = document.querySelector(".asw-menu-header");
        const container = document.querySelector(".asw-container");

        if (header && container) {
            header.style.setProperty("background-color", "#006837", "important");
            container.style.setProperty("font-family", "'Open Sans', sans-serif", "important");
            container.querySelectorAll("*").forEach(el => {
                el.style.setProperty("font-family", "'Open Sans', sans-serif", "important");
            });
        } else {
            setTimeout(styles, 100);
        }
    };
    styles();

    // Menu toggle for responsive navigation
    const menu_toggle = document.querySelector(".menu-toggle");
    const nav_items = document.querySelector(".items");
    const body = document.body;

    menu_toggle.addEventListener("click", () => {
        const expanded = menu_toggle.getAttribute("aria-expanded") === "true";
        menu_toggle.setAttribute("aria-expanded", String(!expanded));
        nav_items.classList.toggle("active");
        body.classList.toggle("no-scroll");
    });
});