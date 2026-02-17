/** @odoo-module **/
import {WebClient} from "@web/webclient/webclient";
import {patch} from "@web/core/utils/patch";

patch(WebClient.prototype, {
    setup() {
        super.setup(...arguments);
        this.env.bus.addEventListener("WEB_CLIENT_READY", () => {
            let isWorkerSupported = "serviceWorker" in navigator;
            if (!isWorkerSupported) {
                console.error(
                    "Service workers are not supported! Maybe you are not using HTTPS or you work in private mode."
                );
            } else {
                navigator.serviceWorker
                    .register("/service-worker.js", {
                        updateViaCache: "none",
                    })
                    .then(function (registration) {
                        console.log("[ServiceWorker] Registered:", registration);
                    })
                    .catch(function (error) {
                        console.log("[ServiceWorker] Registration failed: ", error);
                    });
            }
        });
    }
});

