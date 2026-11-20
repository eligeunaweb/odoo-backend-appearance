import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

function foreground(color) {
    const channels = color.slice(1).match(/../g).map((hex) => {
        const channel = parseInt(hex, 16) / 255;
        return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    return luminance > 0.179 ? "#000000" : "#ffffff";
}

registry.category("services").add("backend_appearance", {
    dependencies: ["orm"],
    start(env, { orm }) {
        const defaults = { accent: "", navbar: "", density: "normal" };
        let published = session.backend_appearance || defaults;
        const state = { ...published };
        const render = (profile) => {
            const root = document.documentElement;
            for (const key of ["accent", "navbar"]) {
                const color = profile[key];
                if (/^#[0-9a-f]{6}$/i.test(color)) {
                    root.style.setProperty(`--ba-${key}`, color);
                    root.style.setProperty(`--ba-${key}-text`, foreground(color));
                    root.setAttribute(`data-ba-${key}`, "");
                } else {
                    root.style.removeProperty(`--ba-${key}`);
                    root.style.removeProperty(`--ba-${key}-text`);
                    root.removeAttribute(`data-ba-${key}`);
                }
            }
            root.dataset.baDensity = profile.density;
        };
        const update = (profile) => {
            Object.assign(state, profile);
            render(state);
        };
        update(published);
        return {
            state,
            preview: update,
            discard() {
                update(published);
            },
            async publish(profile) {
                published = await orm.call("backend.appearance", "publish", [profile]);
                update(published);
            },
            async restore() {
                published = await orm.call("backend.appearance", "restore", []);
                update(published);
            },
        };
    },
});

class AppearancePanel extends Component {
    static template = "backend_appearance.Panel";
    static props = ["*"];

    setup() {
        this.appearance = useService("backend_appearance");
        this.notification = useService("notification");
        this.form = useState({ ...this.appearance.state, busy: false });
    }

    preview() {
        const { accent, navbar, density } = this.form;
        this.appearance.preview({ accent, navbar, density });
        this.notification.add(_t("Preview is active in this tab."), { type: "info" });
    }

    discard() {
        this.appearance.discard();
        Object.assign(this.form, this.appearance.state);
    }

    async save(operation) {
        this.form.busy = true;
        try {
            if (operation === "publish") {
                const { accent, navbar, density } = this.form;
                await this.appearance.publish({ accent, navbar, density });
            } else {
                await this.appearance.restore();
            }
            Object.assign(this.form, this.appearance.state);
            this.notification.add(_t("Appearance settings saved."), { type: "success" });
        } finally {
            this.form.busy = false;
        }
    }
}

registry.category("actions").add("backend_appearance.panel", AppearancePanel);
