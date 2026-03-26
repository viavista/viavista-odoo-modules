# Contributing

Thank you for your interest in contributing!

## How to contribute

1. **Fork** this repository
2. **Create a branch** from `main` for your changes
3. **Make your changes** and add tests if applicable
4. **Run the tests** to make sure nothing is broken:
   ```bash
   odoo-bin server --stop-after-init --test-tags /your_module -d your_db
   ```
5. **Submit a Pull Request** against `main`

## Pull Request guidelines

- Keep PRs focused on a single change
- Include a clear description of what and why
- Add or update tests for new functionality
- Follow existing code style and Odoo conventions
- All modules must pass their test suite before merge

## Reporting issues

Open an issue with:

- Odoo version (Community or Enterprise)
- Steps to reproduce
- Expected vs actual behavior
- Error logs if applicable

## Code style

- Follow [Odoo coding guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html)
- Use `list` (not `tree`) for list views (Odoo 19 convention)
- XML IDs follow the pattern `model_name_view_type`
- All user-facing strings must be translatable (`_()` in Python, standard attributes in XML)

## License

By contributing, you agree that your contributions will be licensed under [LGPL-3.0](LICENSE).
