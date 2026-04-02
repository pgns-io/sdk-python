# Contributing

This repository is synced from a private monorepo. The source of truth for all SDK code lives upstream, and most files here are generated or copied by an automated release pipeline.

Pull requests are welcome on specific parts of the repo. For everything else, open an issue.

## What PRs are welcome on

- `examples/` — new examples, improvements to existing ones
- `docs/` — documentation fixes, additions, clarifications
- `README.md` — typo fixes, improved descriptions, usage examples
- `tests/` — additional test coverage

## What to open an issue for

Most source files (`pgns/`, `pyproject.toml`, etc.) are generated from the upstream monorepo. PRs that modify these files can't be merged directly because the next sync would overwrite them.

If a change is needed in generated code, open an issue describing the problem or desired behavior. The maintainers will apply the fix upstream, and it will ship in the next release.

## How accepted PRs work

When a PR lands on a safe zone listed above, a maintainer reviews it, applies the change in the monorepo, and the next sync publishes it to this repo. The PR itself may be closed rather than merged — the change arrives via the sync pipeline instead.

## Development

Clone the repo and install dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

By contributing, contributions are licensed under the same terms as this project (see [LICENSE](LICENSE)).
