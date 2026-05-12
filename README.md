# Ayiya Skill Cloud

这个仓库用于同步 Codex 本地技能和插件。

## 目录结构

- `skills/`: 对应电脑上的 `C:\Users\<你的用户名>\.codex\skills`
- `plugins/cache/`: 对应电脑上的 `C:\Users\<你的用户名>\.codex\plugins\cache`
- `plugins/cc/`: 对应电脑上的 `C:\Users\<你的用户名>\.codex\plugins\cc`
- `scripts/install-to-codex.ps1`: 把仓库内容复制到本机 Codex 目录的安装脚本

没有提交 `plugins/data/`。这个目录通常是插件运行历史、临时状态和本机记录，不是安装插件必须的内容，也不适合在不同电脑之间同步。

## A 电脑更新方法

在 A 电脑打开 PowerShell，进入这个仓库目录，然后运行：

```powershell
git pull
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install-to-codex.ps1
```

脚本会做三件事：

1. 把仓库的 `skills/` 同步到本机 `.codex\skills`
2. 把仓库的 `plugins/cache/` 同步到本机 `.codex\plugins\cache`
3. 把仓库的 `plugins/cc/` 同步到本机 `.codex\plugins\cc`

同步完成后，重启 Codex，让新技能和插件重新加载。

如果 A 电脑的 Codex 目录不在默认用户目录，可以指定路径：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install-to-codex.ps1 -CodexHome "C:\Users\Administrator\.codex"
```
