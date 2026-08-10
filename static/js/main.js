/* Pray and Obey Ministries: nav behavior, mobile menu, scroll reveal. */

(function () {
  "use strict";

  var nav = document.getElementById("nav");
  var toggle = document.querySelector(".nav__toggle");
  var mobile = document.getElementById("mobile-menu");

  /* Sticky nav shadow */
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Mobile menu */
  if (toggle && mobile) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.setAttribute("aria-label", open ? "Open menu" : "Close menu");
      mobile.hidden = open;
    });

    mobile.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
        mobile.hidden = true;
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !mobile.hidden) {
        toggle.setAttribute("aria-expanded", "false");
        mobile.hidden = true;
        toggle.focus();
      }
    });
  }

  /* Grant budget: live total of the "amount requested" column */
  var budgetInputs = document.querySelectorAll(".js-budget-request");
  var budgetTotal = document.getElementById("budget-total");
  var budgetValue = document.getElementById("budget-total-value");

  if (budgetInputs.length && budgetTotal) {
    var recalc = function () {
      var sum = 0;
      budgetInputs.forEach(function (input) {
        var n = parseFloat(String(input.value).replace(/[^0-9.\-]/g, ""));
        if (!isNaN(n)) { sum += n; }
      });
      var formatted = sum.toLocaleString("en-US", {
        style: "currency",
        currency: "USD"
      });
      budgetTotal.textContent = formatted;
      if (budgetValue) { budgetValue.value = formatted; }
    };
    budgetInputs.forEach(function (input) {
      input.addEventListener("input", recalc);
      input.addEventListener("blur", recalc);
    });
    recalc();
  }

  /* Scroll reveal, disabled when the visitor prefers reduced motion */
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var items = document.querySelectorAll(".reveal");

  if (reduced || !("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("is-visible"); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

  items.forEach(function (el) { observer.observe(el); });
})();
