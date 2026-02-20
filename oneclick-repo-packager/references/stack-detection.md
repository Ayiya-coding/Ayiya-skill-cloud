# Stack Detection Cheatsheet

## Common Files
- Python: pyproject.toml, requirements.txt, setup.py, Pipfile
- Node: package.json, pnpm-lock.yaml, yarn.lock
- Java: pom.xml, build.gradle, gradlew
- Go: go.mod
- Rust: Cargo.toml
- .NET: *.csproj, *.sln
- PHP: composer.json
- Ruby: Gemfile

## Heuristics
- Prefer README instructions if present.
- If multiple stacks exist, choose the one the README calls "quick start".
- If only Dockerfile is documented, ask before using Docker.
