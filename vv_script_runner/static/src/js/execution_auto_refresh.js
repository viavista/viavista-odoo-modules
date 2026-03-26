/** @odoo-module */
import { Component, useState, onWillUnmount, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

class ExecutionAutoRefresh extends Component {
    static template = "vv_script_runner.ExecutionAutoRefresh";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ running: false });
        this._intervalId = null;
        this._pollCount = 0;
        this._maxPolls = 300; // 300 × 2s = 10 minutes

        onMounted(() => {
            if (this.props.record.data.state === "running") {
                this.state.running = true;
                this._startPolling();
            }
        });

        onWillUnmount(() => this._stopPolling());
    }

    _startPolling() {
        if (this._intervalId) return;
        this._pollCount = 0;
        this._intervalId = setInterval(() => this._poll(), 2000);
    }

    _stopPolling() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
    }

    async _poll() {
        this._pollCount++;
        if (this._pollCount > this._maxPolls) {
            this._stopPolling();
            return;
        }
        try {
            const resId = this.props.record.resId;
            if (!resId) return;
            const result = await this.orm.read("script.execution", [resId], ["state"]);
            if (result.length && result[0].state !== "running") {
                this._stopPolling();
                this.state.running = false;
                await this.props.record.load();
            }
        } catch {
            // Network error — keep polling, will retry
        }
    }
}

registry.category("view_widgets").add("execution_auto_refresh", {
    component: ExecutionAutoRefresh,
});
