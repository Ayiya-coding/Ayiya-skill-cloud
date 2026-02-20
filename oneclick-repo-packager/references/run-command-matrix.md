# Install/Run Command Matrix

## Python
- Install: python -m pip install -r requirements.txt
- Run: python app.py / python main.py / uvicorn main:app --host 0.0.0.0 --port 8000
- If pyproject.toml: pip install -e . or poetry install (ask)

## Node
- Install: npm install (or pnpm/yarn if lockfile)
- Run: npm run dev / npm start (use package.json scripts)

## Go
- Install: go mod download
- Run: go run ./cmd/<app> or go run .

## Rust
- Install: cargo build
- Run: cargo run

## Java
- Install/Run: ./mvnw spring-boot:run or ./gradlew bootRun (prefer wrapper)

## .NET
- Install: dotnet restore
- Run: dotnet run --project <path>

## Generic CLI
- If README provides CLI usage, use that as run_cmd.
