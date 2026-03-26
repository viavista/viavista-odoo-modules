# ViaVista Odoo Modules

Open-source Odoo 19 modules by [Viavista d.o.o.](https://viavista.ba)

## Modules

| Module | Summary |
|--------|---------|
| [vv_script_runner](vv_script_runner/) | Run Python scripts from within Odoo with dry-run, timeout, change tracking, and full audit logging |

## Installation

Clone this repository into your Odoo addons path:

```bash
git clone https://github.com/viavista/vv-odoo-modules.git
```

Add the path to your Odoo configuration:

```ini
[options]
addons_path = /path/to/vv-odoo-modules,...
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
