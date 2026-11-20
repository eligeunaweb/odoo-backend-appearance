/** @odoo-module **/

import { Component, onWillStart, useEffect, useState } from "@odoo/owl";
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
    navbar_photo: "",
    apps_menu: "standard",
    apps_menu_background: "#182337",
    apps_menu_highlight: "#34465f",
    navbar_mode: "color",
    photo_position: 50,
    text_size: "standard",
    logo: "",
    favicon: "",
};

function imageUrl(data) {
    return typeof data === "string" && /^\/9j\/[A-Za-z0-9+/]+={0,2}$/.test(data)
        ? `data:image/jpeg;base64,${data}`
        : "";
}

function foreground(color) {
    const channels = color.slice(1).match(/../g).map((hex) => {
        const channel = parseInt(hex, 16) / 255;
        return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    return luminance > 0.179 ? "#000000" : "#ffffff";
}

registry.category("services").add("euw_backend_appearance", {
    dependencies: ["orm", "company"],
    async start(env, { orm }) {
        let published = { ...DEFAULT_PROFILE, ...session.euw_backend_appearance };
        let draft = null;
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
            const photo = profile.navbar_mode === "photo" && imageUrl(profile.navbar_photo);
            const hasPhoto = Boolean(photo);
            root.toggleAttribute("data-ba-photo", hasPhoto);
            if (hasPhoto) {
                root.style.setProperty("--ba-navbar-photo", `url("${photo}")`);
            } else {
                root.style.removeProperty("--ba-navbar-photo");
            }
            root.style.setProperty("--ba-photo-position", `${profile.photo_position}%`);
            root.dataset.baText = profile.text_size;
            const logo = imageUrl(profile.logo);
            root.toggleAttribute("data-ba-logo", Boolean(logo));
            if (logo) {
                root.style.setProperty("--ba-logo", `url("${logo}")`);
            } else {
                root.style.removeProperty("--ba-logo");
            }
            const favicon = imageUrl(profile.favicon);
            const icon = document.getElementById("ba-favicon");
            if (favicon) {
                const link = icon || document.createElement("link");
                link.id = "ba-favicon";
                link.rel = "icon";
                link.href = favicon;
                if (!icon) {
                    document.head.append(link);
                }
            } else {
                icon?.remove();
            }
            root.dataset.baAppsMenu = profile.apps_menu;
            for (const [field, name] of [
                ["apps_menu_background", "bg"],
                ["apps_menu_highlight", "hover"],
            ]) {
                const color = profile[field];
                if (profile.apps_menu === "custom" && /^#[0-9a-f]{6}$/i.test(color)) {
                    root.style.setProperty(`--ba-apps-${name}`, color);
                    root.style.setProperty(`--ba-apps-${name}-text`, foreground(color));
                } else {
                    root.style.removeProperty(`--ba-apps-${name}`);
                    root.style.removeProperty(`--ba-apps-${name}-text`);
                }
            }
            if (profile.navbar_mode === "pattern" && PATTERNS.includes(profile.navbar_pattern)) {
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
        const call = (method, args) => orm.call("euw.backend.appearance", method, args);
        try {
            published = await call("get_current_profile", []);
        } catch {
            // Keep the server bootstrap profile if the company lookup fails.
        }
        update(published);
        const refresh = async () => {
            published = (await call("get_editor", ["company"])).profile;
            draft = null;
            update(published);
        };
        return {
            state,
            call,
            get draft() {
                return draft;
            },
            preview(profile, scope) {
                draft = { profile, scope };
                update(profile);
            },
            discard() {
                draft = null;
                update(published);
            },
            async publish(profile, scope) {
                await call("publish", [profile, scope]);
                await refresh();
            },
            async restore(scope) {
                await call("restore", [scope]);
                await refresh();
            },
        };
    },
});

class AppearancePanel extends Component {
    static template = "euw_backend_appearance.Panel";
    static props = ["*"];

    setup() {
        this.appearance = useService("euw_backend_appearance");
        this.notification = useService("notification");
        this.form = useState({ ...this.appearance.state });
        this.editor = useState({
            busy: false, tab: "bar", scope: "global", saved: "", themes: [], themeName: "", selectedTheme: "",
            comparison: "after", previewOpen: false, inheritsGlobal: false,
        });
        this.companyName = useService("company").currentCompany.name;
        this.tabs = [
            { id: "bar", name: _t("Top bar") },
            { id: "menu", name: _t("Apps menu") },
            { id: "workspace", name: _t("Workspace") },
            { id: "themes", name: _t("Themes") },
        ];
        this.images = [
            { id: "logo", label: _t("Top bar logo") },
            { id: "favicon", label: _t("Browser tab icon") },
        ];
        this.menuStyles = [
            { id: "standard", name: _t("Odoo default") },
            { id: "light", name: _t("Light") },
            { id: "dark", name: _t("Dark") },
            { id: "custom", name: _t("Custom") },
        ];
        this.patterns = [
            { id: "solid", label: _t("Solid") },
            { id: "dots", label: _t("Dots") },
            { id: "grid", label: _t("Grid") },
            { id: "diagonal", label: _t("Diagonals") },
            { id: "waves", label: _t("Waves") },
        ];
        onWillStart(async () => {
            const draft = this.appearance.draft;
            await this.loadEditor(draft?.scope || "global");
            if (draft) {
                Object.assign(this.form, draft.profile);
            }
        });
        useEffect(() => {
            if (this.dirty) {
                this.appearance.preview(this.profile, this.editor.scope);
            } else {
                this.appearance.discard();
            }
        }, () => [this.serializedProfile, this.editor.saved]);
    }

    async loadEditor(scope) {
        const { profile, themes, inherits_global } = await this.appearance.call("get_editor", [scope]);
        this.editor.scope = scope;
        this.editor.themes = themes;
        this.editor.inheritsGlobal = Boolean(inherits_global);
        this.editor.comparison = "after";
        Object.assign(this.form, profile);
        this.editor.saved = this.serializedProfile;
    }

    switchTab(event) {
        this.editor.tab = event.currentTarget.dataset.section;
    }

    toggleSample() {
        this.editor.previewOpen = !this.editor.previewOpen;
    }

    compareSample(event) {
        this.editor.comparison = event.currentTarget.dataset.comparison;
    }

    get sample() {
        const profile = this.editor.comparison === "before" && this.editor.saved
            ? JSON.parse(this.editor.saved) : this.profile;
        const bar = profile.navbar || "#71639e";
        const accent = profile.accent || "#71639e";
        const ink = foreground(bar) === "#ffffff" ? "0,0,0" : "255,255,255";
        const menu = {
            standard: ["#ffffff", "#e9ecef"],
            light: ["#f8fafc", "#e2ebf5"],
            dark: ["#182337", "#34465f"],
            custom: [profile.apps_menu_background, profile.apps_menu_highlight],
        }[profile.apps_menu];
        const photo = profile.navbar_mode === "photo" ? imageUrl(profile.navbar_photo) : "";
        return {
            photo,
            logo: imageUrl(profile.logo),
            pattern: profile.navbar_mode === "pattern" ? profile.navbar_pattern : "",
            density: profile.density,
            text: profile.text_size,
            style: [
                `--ba-sample-bar:${bar}`,
                `--ba-sample-bar-text:${photo ? "#ffffff" : foreground(bar)}`,
                `--ba-sample-accent:${accent}`,
                `--ba-sample-accent-text:${foreground(accent)}`,
                `--ba-pattern-ink:rgba(${ink},${profile.pattern_intensity / (profile.navbar ? 250 : 600)})`,
                `--ba-sample-menu:${menu[0]}`,
                `--ba-sample-menu-text:${foreground(menu[0])}`,
                `--ba-sample-highlight:${menu[1]}`,
                `--ba-sample-highlight-text:${foreground(menu[1])}`,
                `--ba-photo-position:${profile.photo_position}%`,
                photo && `--ba-sample-photo:url("${photo}")`,
            ].filter(Boolean).join(";"),
        };
    }

    switchScope(event) {
        const scope = event.currentTarget.value;
        return this.run(() => this.loadEditor(scope));
    }

    selectPattern(event) {
        this.form.navbar_pattern = event.currentTarget.dataset.pattern;
    }

    selectMenu(event) {
        this.form.apps_menu = event.currentTarget.dataset.menuStyle;
    }

    async uploadPhoto(event) {
        const input = event.currentTarget;
        const file = input.files[0];
        const field = input.dataset.field;
        input.value = "";
        if (!file) {
            return;
        }
        if (file.size > 4 * 1024 * 1024) {
            this.notification.add(_t("Choose an image of up to 4 MB."), { type: "warning" });
            return;
        }
        await this.run(async () => {
            const uri = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => reject(reader.error);
                reader.readAsDataURL(file);
            });
            this.form[field] = await this.appearance.call("normalize_photo", [uri.split(",")[1], field]);
        });
    }

    removePhoto(event) {
        const field = event.currentTarget.dataset.field;
        this.form[field] = "";
        if (field === "navbar_photo") {
            this.form.navbar_mode = this.form.navbar_pattern === "solid" ? "color" : "pattern";
        }
    }

    get serializedProfile() {
        return JSON.stringify(this.profile);
    }

    get dirty() {
        return this.editor.saved && this.serializedProfile !== this.editor.saved;
    }

    get profile() {
        return {
            ...this.form,
            pattern_intensity: Number(this.form.pattern_intensity),
            photo_position: Number(this.form.photo_position),
        };
    }

    discard() {
        this.appearance.discard();
        Object.assign(this.form, JSON.parse(this.editor.saved));
    }

    apply() {
        return this.run(async () => {
            await this.appearance.publish(this.profile, this.editor.scope);
            await this.loadEditor(this.editor.scope);
            this.notification.add(_t("Appearance settings saved."), { type: "success" });
        });
    }

    restore() {
        return this.run(async () => {
            await this.appearance.restore(this.editor.scope);
            await this.loadEditor(this.editor.scope);
            this.notification.add(_t("Appearance settings saved."), { type: "success" });
        });
    }

    saveTheme() {
        return this.run(async () => {
            this.editor.themes = await this.appearance.call("save_theme", [this.editor.themeName, this.profile]);
            this.editor.selectedTheme = this.editor.themeName.trim();
        });
    }

    loadTheme() {
        return this.run(async () => {
            Object.assign(this.form, await this.appearance.call("load_theme", [this.editor.selectedTheme]));
        });
    }

    deleteTheme() {
        return this.run(async () => {
            this.editor.themes = await this.appearance.call("delete_theme", [this.editor.selectedTheme]);
            this.editor.selectedTheme = "";
        });
    }

    exportTheme() {
        const blob = new Blob([JSON.stringify({ version: 1, profile: this.profile }, null, 2)], {
            type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "odoo-appearance.json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    async importTheme(event) {
        const input = event.currentTarget;
        const file = input.files[0];
        input.value = "";
        if (!file) {
            return;
        }
        await this.run(async () => {
            let data;
            try {
                if (file.size > 1_000_000) {
                    throw new Error("size");
                }
                data = JSON.parse(await file.text());
            } catch {
                this.notification.add(_t("Choose an appearance JSON file under 1 MB."), { type: "warning" });
                return;
            }
            Object.assign(this.form, await this.appearance.call("import_theme", [data]));
        });
    }

    async run(operation) {
        this.editor.busy = true;
        try {
            await operation();
        } finally {
            this.editor.busy = false;
        }
    }
}

registry.category("actions").add("euw_backend_appearance.panel", AppearancePanel);
