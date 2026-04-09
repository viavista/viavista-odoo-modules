# ViaVista Odoo Modules

Open-source Odoo 19 modules by [Viavista d.o.o.](https://viavista.ba)

## Modules

| Module | Summary |
|--------|---------|
| [viavista_monitoring_logs](viavista_monitoring_logs/) | Enhanced error tracking with RPC error capture, log retention, and backup agent integration |
| [viavista_script_runner](viavista_script_runner/) | Run Python scripts from within Odoo with dry-run, timeout, change tracking, and full audit logging |
| [viavista_ui](viavista_ui/) | Per-warehouse stock on product kanban and per-user hidden menus |

## Installation

Clone this repository into your Odoo addons path:

```bash
git clone https://github.com/viavista/viavista-odoo-modules.git
```

Add the path to your Odoo configuration:

```ini
[options]
addons_path = /path/to/viavista-odoo-modules,...
```

Then install the desired module from **Settings > Technical > Modules**.

## Requirements

- Odoo 19.0 (Community or Enterprise)
- Python 3.12+
- PostgreSQL 14+

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[LGPL-3.0](LICENSE)
