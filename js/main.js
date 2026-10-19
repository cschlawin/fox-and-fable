/**
 * Fox & Fable — homepage behaviour
 * Vanilla JS, no dependencies. Loaded from 'self' only (see CSP).
 *  1. Progressive-enhancement flag (.no-js → .js)
 *  2. Mobile navigation toggle
 *  3. Consultation form: client-side validation + mockup success state
 *
 * Security notes:
 *  - User input is only ever written to the page with textContent, never innerHTML.
 *  - Client-side validation improves UX only; it is NOT a security control.
 *    A real backend must re-validate, rate-limit, and spam-filter every submission.
 */
(function () {
  "use strict";

  // 1. Progressive enhancement ------------------------------------------------
  document.documentElement.classList.replace("no-js", "js");

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initForm();
    var year = document.getElementById("year");
    if (year) year.textContent = String(new Date().getFullYear());
  });

  // 2. Mobile navigation -------------------------------------------------------
  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("primary-nav");
    if (!toggle || !nav) return;
    var label = toggle.querySelector(".visually-hidden");

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      if (label) label.textContent = open ? "Close menu" : "Menu";
    }

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Close after choosing a link, on Escape, or when resizing to desktop.
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
    window.matchMedia("(min-width: 1024px)").addEventListener("change", function (mq) {
      if (mq.matches) setOpen(false);
    });
  }

  // 3. Consultation form -------------------------------------------------------
  var EMAIL_RE = /^[^\s@<>()[\]\\,;:"]+@[^\s@<>()[\]\\,;:"]+\.[A-Za-z]{2,}$/;
  var PHONE_RE = /^[0-9+().\-\s]{7,20}$/;
  // Strip control characters (except newline/tab in the message) and trim.
  function clean(value, allowNewlines) {
    var re = allowNewlines ? /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g : /[\u0000-\u001F\u007F]/g;
    return String(value).replace(re, "").trim();
  }

  var RULES = {
    name:     { required: "Please tell us your name.", max: 80 },
    email:    { required: "Please add an email so we can reply.", max: 254,
                test: function (v) { return EMAIL_RE.test(v); }, invalid: "That email doesn't look quite right. Try name@example.com." },
    phone:    { max: 20, test: function (v) { return v === "" || (PHONE_RE.test(v) && v.replace(/\D/g, "").length >= 7); },
                invalid: "Please use digits, spaces, or + ( ) - only, at least 7 digits." },
    city:     { required: "Which city is the project in?", max: 60 },
    room:     { required: "Please choose a room type." },
    project:  { required: "Please choose a project type." },
    budget:   { required: "Please choose a budget range." },
    timeline: { required: "Please choose a timeline." },
    message:  { max: 2000, multiline: true }
  };

  function initForm() {
    var form = document.getElementById("consult-form");
    if (!form) return;
    var status = document.getElementById("form-status");
    var message = form.elements.message;
    var counter = document.getElementById("message-count");

    if (message && counter) {
      message.addEventListener("input", function () {
        counter.textContent = message.value.length + " / " + RULES.message.max + " characters";
      });
    }

    // Re-validate a field as the visitor fixes it (only after it was flagged).
    form.addEventListener("input", function (e) {
      var field = e.target;
      if (field.getAttribute("aria-invalid") === "true") validateField(form, field.name);
    });
    form.addEventListener("change", function (e) {
      if (e.target.getAttribute("aria-invalid") === "true") validateField(form, e.target.name);
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault(); // Mockup: nothing is sent anywhere.

      // Honeypot: real people never see this field. Silently "succeed" for bots.
      if (form.elements.website && form.elements.website.value !== "") {
        form.reset();
        return;
      }

      var firstInvalid = null;
      var errors = 0;
      Object.keys(RULES).forEach(function (name) {
        if (!validateField(form, name)) {
          errors++;
          if (!firstInvalid) firstInvalid = form.elements[name];
        }
      });

      status.className = "form-status";
      status.replaceChildren();

      if (errors) {
        status.classList.add("is-error");
        status.textContent = errors === 1
          ? "One field needs a quick look before we can continue."
          : errors + " fields need a quick look before we can continue.";
        if (firstInvalid) firstInvalid.focus();
        return;
      }

      // Success state. Built with DOM nodes + textContent (never innerHTML).
      var firstName = clean(form.elements.name.value).split(/\s+/)[0];
      var heading = document.createElement("strong");
      heading.textContent = "Thank you, " + firstName + ".";
      var body = document.createElement("span");
      body.textContent = " Your story has been noted. (Mockup only: nothing was sent. A live site would deliver this to the Fox & Fable team.)";
      status.classList.add("is-success");
      status.append(heading, body);
      form.reset();
      if (counter) counter.textContent = "0 / " + RULES.message.max + " characters";
      status.setAttribute("tabindex", "-1");
      status.focus();
    });
  }

  function validateField(form, name) {
    var field = form.elements[name];
    var rule = RULES[name];
    if (!field || !rule) return true;

    var value = clean(field.value, rule.multiline);
    var msg = "";
    if (rule.required && value === "") msg = rule.required;
    else if (rule.max && value.length > rule.max) msg = "Please keep this under " + rule.max + " characters.";
    else if (rule.test && value !== "" && !rule.test(value)) msg = rule.invalid;

    var error = document.getElementById(name + "-error");
    if (msg) {
      field.setAttribute("aria-invalid", "true");
      if (error) error.textContent = msg;
      return false;
    }
    field.removeAttribute("aria-invalid");
    if (error) error.textContent = "";
    return true;
  }
})();
