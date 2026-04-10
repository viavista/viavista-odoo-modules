import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { Plugin } from "@html_editor/plugin";
import { BaseCoverPropertiesAction } from "@website/builder/plugins/options/cover_properties_option_plugin";

const VIS_CLASSES = [
    "o_vv_cover_hidden_desktop",
    "o_snippet_desktop_invisible",
    "o_vv_cover_hidden_mobile",
    "o_snippet_mobile_invisible",
];

// --- Action: toggle cover visibility per device ---

class ToggleCoverVisibilityAction extends BaseCoverPropertiesAction {
    static id = "toggleCoverVisibility";

    apply({ editingElement, params: { mainParam: visibility } }) {
        editingElement.classList.remove(...VIS_CLASSES);

        if (visibility === "no_desktop" || visibility === "hidden") {
            editingElement.classList.add(
                "o_vv_cover_hidden_desktop",
                "o_snippet_desktop_invisible"
            );
        }
        if (visibility === "no_mobile" || visibility === "hidden") {
            editingElement.classList.add(
                "o_vv_cover_hidden_mobile",
                "o_snippet_mobile_invisible"
            );
        }

        this.markCoverPropertiesToBeSaved({ editingElement });
    }

    isApplied({ editingElement, params: { mainParam: visibility } }) {
        const hd = editingElement.classList.contains("o_vv_cover_hidden_desktop");
        const hm = editingElement.classList.contains("o_vv_cover_hidden_mobile");
        if (visibility === "") return !hd && !hm;
        if (visibility === "no_desktop") return hd && !hm;
        if (visibility === "no_mobile") return !hd && hm;
        if (visibility === "hidden") return hd && hm;
        return false;
    }
}

// --- Plugin: register the action ---

class ViavistaCoverVisibilityPlugin extends Plugin {
    static id = "viavistaCoverVisibility";
    resources = {
        builder_actions: {
            ToggleCoverVisibilityAction,
        },
    };
}

registry
    .category("website-plugins")
    .add(ViavistaCoverVisibilityPlugin.id, ViavistaCoverVisibilityPlugin);

// --- Patch readCoverPoperties to persist visibility classes in resize_class ---

const CoverPropertiesPlugin = registry
    .category("website-plugins")
    .get("coverPropertiesOption");

patch(CoverPropertiesPlugin.prototype, {
    readCoverPoperties(el) {
        const result = super.readCoverPoperties(el);
        const extra = VIS_CLASSES.filter((cls) => el.classList.contains(cls));
        if (extra.length) {
            result.resize_class = (
                (result.resize_class || "") +
                " " +
                extra.join(" ")
            ).trim();
        }
        return result;
    },
});
