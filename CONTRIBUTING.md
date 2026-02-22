# Contributing to AFL (Agent Failure Mode)

Thanks for helping make agent behavior more honest.

## What we want
- Bug fixes, especially around hook edge cases and cross-platform behavior
- Improvements to the evaluation prompt suite + scoring rubric
- Better documentation for real-world "cannot complete / cannot verify" scenarios
- Vendor-agnostic abstractions (so this can extend beyond the host agent)

## What we *don't* want
- Claims of "this eliminates hallucinations" without measurement
- Features that depend on proprietary/internal model confidence scores

## Development setup
```bash
python3 -m unittest discover -s tests -q
```

No external dependencies are required; please keep it stdlib-only unless there is a strong reason.

## PR checklist
- [ ] Tests updated or added
- [ ] Docs updated (if behavior changes)
- [ ] Policy schema changes documented in `docs/02-design.md`
- [ ] Any new "prompt triggers" include a rationale and a failure mode category

## Style
- Keep hook scripts small and explicit.
- Prefer readable policy over clever heuristics.

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
