(function () {
    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    function injectCSRF() {
        if (!document.body) return;
        var token = getCookie("unsaid_csrf");
        if (!token) return;
        document.querySelectorAll("form").forEach(function (form) {
            if (form.querySelector('input[name="csrf_token"]')) return;
            var input = document.createElement("input");
            input.type = "hidden";
            input.name = "csrf_token";
            input.value = token;
            form.appendChild(input);
        });
    }

    document.addEventListener("htmx:configRequest", function (event) {
        var token = getCookie("unsaid_csrf");
        if (!token || !event.detail) return;
        event.detail.headers = event.detail.headers || {};
        event.detail.headers["X-CSRF-Token"] = token;
    });

    document.addEventListener("DOMContentLoaded", injectCSRF);
    document.body && document.body.addEventListener("htmx:afterSwap", injectCSRF);
    injectCSRF();
})();
