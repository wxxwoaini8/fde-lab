# Git 提交分步清单

# Git 提交分步清单

> 每次提交都按这个顺序走一遍。命令在 Git Bash 里敲。
> 这套流程挡住的典型事故：把 `.env` 密码、几百 MB 安装包、临时测试文件提交上去。

---

## 阶段 1 · 确认位置

```bash
cd /e/FDE
pwd
```

| 项 | 内容 |
| --- | --- |
| 在哪敲 | Git Bash |
| 成功 | 输出 `/e/FDE` |
| 失败 | 显示别的路径 → `cd` 没生效，重敲 |

---

## 阶段 2 · 看现状

```bash
git status
```

| 项 | 内容 |
| --- | --- |
| 成功 | `On branch main`，下面列出改动 |
| 看什么 | `Untracked files`（新文件，Git 还不管）/ `Changes not staged`（改过没暂存） |
| 失败 | `not a git repository` → 当前目录不是仓库，回阶段 1 |

---

## 阶段 3 · 预演（最关键的一步）

```bash
git add -A --dry-run
```

| 项 | 内容 |
| --- | --- |
| 成功 | 一行一个 `add '文件名'`，列出「如果全加会加什么」 |
| 停下来想 | 里面有没有不该进仓库的？密码、大文件、临时测试 |
| 有 | 记下路径，阶段 5 用精确添加跳过它 |

这一步只是预演，**不会真的加任何东西**，随便跑。

---

## 阶段 4 · 确认敏感文件被挡住

```bash
git check-ignore -v docker/.env
```

| 项 | 内容 |
| --- | --- |
| 成功 | 输出 `.gitignore:18:.env	docker/.env`（说明被第 18 行规则挡住） |
| 没输出 | **没被忽略**，绝不能提交，先去补 `.gitignore` |
| 换文件 | 把路径换成你要确认的那个敏感文件 |

---

## 阶段 5 · 精确暂存

```bash
git add check_env.py docker/
```

| 项 | 内容 |
| --- | --- |
| 为什么不用 `-A` | 会把阶段 3 看到的临时文件一起塞进去 |
| 成功 | 没有输出就是成功（Git 的沉默是金） |
| 失败 | `pathspec ... did not match` → 路径打错或文件不在当前目录 |

---

## 阶段 6 · 复核暂存区

```bash
git status --short
git diff --cached --name-only
```

| 项 | 内容 |
| --- | --- |
| 成功 | 每行开头 `A`（新增）/ `M`（修改）；`??` 是未暂存的 |
| 最后确认 | `diff --cached --name-only` 的清单 = 即将提交的全部内容 |
| 多了一个 | `git restore --staged 文件名` 撤掉 |

---

## 阶段 7 · 提交

单行：

```bash
git commit -m "chore: 加环境自检脚本与本地开发数据库编排"
```

多行（标题 + 正文）：

```bash
git commit -m "chore: 加环境自检脚本" -m "- check_env.py：23 项自检
- docker/compose.yml：PostgreSQL 编排"
```

| 项 | 内容 |
| --- | --- |
| 成功 | `[main xxxxxxx] chore: ...` 加 `3 files changed, 357 insertions(+)` |
| 失败 | `nothing added to commit` → 阶段 5 没成功，回去重做 |

**提交信息格式**：`类型: 做了什么`，正文写**为什么**。
常用类型：`feat` 新功能 / `fix` 修 bug / `docs` 文档 / `chore` 杂务 / `refactor` 重构 / `test` 测试。

---

## 阶段 8 · 推送并反向验证

```bash
git push
git status
```

```bash
git ls-remote origin main
git ls-tree -r origin/main --name-only
```

| 项 | 内容 |
| --- | --- |
| 成功 | `main -> main`，`git status` 显示 `up to date with 'origin/main'` |
| 为什么要反向验证 | 终端说成功但网页没变的情况真实存在（推错账号/仓库） |
| 教材原话 | 「推送完必须去网页确认一次，只看终端输出不算数」 |

---

## 出错了怎么办

| 情况 | 命令 |
| --- | --- |
| 加错了，还没提交 | `git restore --staged 文件名` |
| 提交了，还没推送 | `git reset --soft HEAD~1` |
| 只想改提交信息 | `git commit --amend` |
| 已经推送到远端 | 密钥类：立即轮换；大文件：`git filter-repo` 重写历史（协作仓库代价大） |

---

## 一句话判据

> 明天换台电脑，从零 `git clone` 下来，只靠仓库里的东西能不能跑起来？
> 能 → 提交得对。不能 → 少了东西，或交多了东西。

---

## 不要提交什么（速记）

| 类别 | 例子 |
| --- | --- |
| 密钥凭据 | `.env`、`*.pem`、`*.key`、`secrets.*` |
| 可重建 | `.venv/`、`node_modules/`、`__pycache__/`、`dist/`、`*.pyc` |
| 大文件 | 安装包、视频、模型权重 |
| 隐私数据 | 客户真实数据（脱敏前） |
| 机器相关 | `.vscode/`、`.idea/`、日志 |
