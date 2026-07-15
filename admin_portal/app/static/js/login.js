(function () {
    function initPasswordToggle() {
        var toggle = document.getElementById("sfa-password-toggle");
        var input = document.getElementById("sfa-password-input");
        if (!toggle || !input) { return; }

        var showIcon = toggle.querySelector("[data-icon-show]");
        var hideIcon = toggle.querySelector("[data-icon-hide]");

        toggle.addEventListener("click", function () {
            var isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            toggle.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
            toggle.setAttribute("aria-pressed", isPassword ? "true" : "false");
            showIcon.hidden = isPassword;
            hideIcon.hidden = !isPassword;
            input.focus({ preventScroll: true });
        });
    }

    function initCapsLockDetection() {
        var input = document.getElementById("sfa-password-input");
        var hint = document.getElementById("sfa-capslock-hint");
        if (!input || !hint) { return; }

        function check(event) {
            if (typeof event.getModifierState !== "function") { return; }
            hint.hidden = !event.getModifierState("CapsLock");
        }

        input.addEventListener("keyup", check);
        input.addEventListener("keydown", check);
        input.addEventListener("blur", function () { hint.hidden = true; });
    }

    function initForgotPasswordTip() {
        var btn = document.getElementById("sfa-forgot-btn");
        var tip = document.getElementById("sfa-forgot-tip");
        if (!btn || !tip) { return; }

        btn.addEventListener("click", function () {
            var isHidden = tip.hidden;
            tip.hidden = !isHidden;
            btn.setAttribute("aria-expanded", isHidden ? "true" : "false");
        });
    }

    function initRipple() {
        var btn = document.getElementById("sfa-submit-btn");
        if (!btn) { return; }

        btn.addEventListener("click", function (event) {
            var rect = btn.getBoundingClientRect();
            var size = Math.max(rect.width, rect.height);
            var ripple = document.createElement("span");
            ripple.className = "sfa-ripple";
            ripple.style.width = ripple.style.height = size + "px";
            ripple.style.left = (event.clientX - rect.left - size / 2) + "px";
            ripple.style.top = (event.clientY - rect.top - size / 2) + "px";
            btn.appendChild(ripple);
            ripple.addEventListener("animationend", function () { ripple.remove(); });
        });
    }

    function initSubmitLoadingState() {
        var form = document.getElementById("sfa-login-form");
        var btn = document.getElementById("sfa-submit-btn");
        if (!form || !btn) { return; }

        form.addEventListener("submit", function () {
            if (typeof form.reportValidity === "function" && !form.reportValidity()) { return; }
            btn.disabled = true;
            btn.dataset.originalText = btn.textContent;
            btn.innerHTML = '<span class="sfa-spinner" aria-hidden="true"></span>Signing in…';
        });
    }

    function initFooterYear() {
        var el = document.getElementById("sfa-current-year");
        if (!el) { return; }
        el.textContent = new Date().getFullYear();
    }

    document.addEventListener("DOMContentLoaded", function () {
        initPasswordToggle();
        initCapsLockDetection();
        initForgotPasswordTip();
        initRipple();
        initSubmitLoadingState();
        initFooterYear();
    });
})();
