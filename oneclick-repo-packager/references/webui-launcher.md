# WebUI Launcher (assets/webui-launcher)

Files:
- app.py: Flask server
- config.json: fill commands
- requirements.txt: Flask dependency
- templates/index.html + static: UI

## config.json fields
- working_dir: where install/run commands execute (usually ".." for repo root)
- install_cmd: shell command to install deps (use "SKIP" to disable)
- run_cmd: shell command to start app (use "SKIP" to disable)
- app_url: optional URL to open after app starts (e.g., http://localhost:3000)
- webui_port: default 7860

## Usage
1. Copy webui-launcher to repo/webui
2. Edit config.json with commands
3. run.ps1/run.sh installs webui deps and opens http://localhost:<webui_port>
4. Use WebUI buttons to install/run and view logs
