import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const PATTERNS = ["dots", "grid", "diagonal", "waves"];
const DEFAULT_PROFILE = {
    accent: "",
    navbar: "",
    density: "normal",
    navbar_pattern: "solid",
    pattern_intensity: 45,
};

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
        let published = { ...DEFAULT_PROFILE, ...session.backend_appearance };
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
            if (PATTERNS.includes(profile.navbar_pattern)) {
                root.dataset.baPattern = profile.navbar_pattern;
                root.style.setProperty("--ba-pattern-opacity", profile.pattern_intensity / 250);
                if (root.hasAttribute("data-ba-navbar")) {
                    const shade = foreground(profile.navbar) === "#ffffff" ? "0, 0, 0" : "255, 255, 255";
                    root.style.setProperty("--ba-pattern-rgb", shade);
                } else {
                    root.style.removeProperty("--ba-pattern-rgb");
                    root.style.setProperty("--ba-pattern-opacity", profile.pattern_intensity / 600);
                }
            } else {
                root.removeAttribute("data-ba-pattern");
                root.style.removeProperty("--ba-pattern-opacity");
                root.style.removeProperty("--ba-pattern-rgb");
            }
        };
        const update = (profile) => {
            Object.assign(state, DEFAULT_PROFILE, profile);
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
        this.patterns = [
            { id: "solid", label: _t("Solid") },
            { id: "dots", label: _t("Dots") },
            { id: "grid", label: _t("Grid") },
            { id: "diagonal", label: _t("Diagonals") },
            { id: "waves", label: _t("Waves") },
        ];
    }

    selectPattern(event) {
        this.form.navbar_pattern = event.currentTarget.dataset.pattern;
    }

    preview() {
        this.appearance.preview(this.profile);
        this.notification.add(_t("Preview is active in this tab."), { type: "info" });
    }

    get profile() {
        const { busy, pattern_intensity, ...values } = this.form;
        return { ...values, pattern_intensity: Number(pattern_intensity) };
    }

    discard() {
        this.appearance.discard();
        Object.assign(this.form, this.appearance.state);
    }

    apply() {
        return this.save(() => this.appearance.publish(this.profile));
    }

    restore() {
        return this.save(() => this.appearance.restore());
    }

    async save(operation) {
        this.form.busy = true;
        try {
            await operation();
            Object.assign(this.form, this.appearance.state);
            this.notification.add(_t("Appearance settings saved."), { type: "success" });
        } finally {
            this.form.busy = false;
        }
    }
}

registry.category("actions").add("backend_appearance.panel", AppearancePanel);
