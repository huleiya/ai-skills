# 本机技能备份

收录 Claude、Agents、Codex、Workbuddy、Gemini 用户技能目录中的技能。`skills/` 对同名技能优先采用 Claude 母版，`variants/agents/` 保留内容不同的 Agents 副本。`synced/` 技能保留原有路径。

不收录应用内置 `.system`、插件运行缓存、嵌套 Git 数据、依赖缓存或凭据。

## 多设备同步

个人技能远程仓库固定为 `https://github.com/huleiya/ai-skills.git`。
每台设备将仓库克隆到 `~/.claude/ai-skills`。仓库的 `skills/` 用于版本管理，
`~/.claude/skills` 是本地母版，`~/.codex/skills` 和 `~/.workbuddy/skills` 是副本。
两种目录层级不同，不要在 `~/.claude/skills` 直接执行仓库的 Git 命令。

首次配置（需要 Git 和 Python 3.9+；Windows 的 `~` 替换为用户目录）：

```sh
git clone https://github.com/huleiya/ai-skills.git ~/.claude/ai-skills
cd ~/.claude/ai-skills
python scripts/sync-skills.py install jd-resume-tailor
```

在另一台设备使用前，先检查仓库工作区；干净时拉取，再安装需要的技能：

```sh
git status --short
git pull --ff-only origin main
python scripts/sync-skills.py install jd-resume-tailor
```

同步脚本支持一次指定多个技能名。仅同步指定技能，覆盖前备份不同的文件到
`~/.cache/ai-skills-backups/`，不删除各端独有文件，不自动提交或推送。
同步前先检查各端修改；不同设备同时修改同一技能时，先人工合并，再安装。
脚本跳过常见凭据和缓存；提交前仍需检查差异，不收录本机私有资料索引。
`manifest.json` 保留首次备份的统计信息，不是实时同步状态。

修改本地母版后，将该技能回收至仓库：

```sh
cd ~/.claude/ai-skills
git switch main
git pull --ff-only origin main
git switch -c skill/update-resume
python scripts/sync-skills.py collect jd-resume-tailor
git diff
git add -- skills/jd-resume-tailor
git commit -m "feat: 更新简历改写技能"
git switch main
git pull --ff-only origin main
git merge --no-ff skill/update-resume
git push origin main
python scripts/sync-skills.py install jd-resume-tailor
```

如修改源是 Codex 或 Workbuddy，回收时分别加 `--source codex` 或
`--source workbuddy`，随后执行 `install` 同步回 Claude 母版及另外两端。
功能分支名按每次修改另取；主干无法快进更新时先处理分叉，不强推。
`variants/` 只作历史差异存档，不自动覆盖 `skills/` 中的版本。
