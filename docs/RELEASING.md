# Releasing / Publishing

## 1) Create a GitHub repo
- Create a new repository named `afl` (or your preferred name).
- Add this folder's contents.

## 2) Push
```bash
git init
git add .
git commit -m "Initial release: AFL (Agent Failure Mode)"
git branch -M main
git remote add origin git@github.com:<you-or-org>/afl.git
git push -u origin main
```

## 3) Tag a release
```bash
git tag v0.1.0
git push origin v0.1.0
```

## 4) Attach a zip to the GitHub release (optional)
```bash
make package
```
This writes `dist/afl.zip`.
