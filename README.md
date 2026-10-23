# fde-lab

从产品经理到 FDE 的 24 周转型学习工作区。每周一个子目录，放代码、笔记和复盘。

## 环境

- Python 3.12，虚拟环境在 `.venv`（由 uv 管理，不进版本库）
- Node.js 24 LTS（第 3 周起用）
- 编辑器：CodeBuddy CN

## 目录

| 目录 | 内容 |
| --- | --- |
| `docs/` | 教材：24 周方案 + 分册 00~04，共 6 本（只读，先看 `docs/README.md`） |
| `notes/` | 自己的笔记：总览说明、每周要点速查、项目推进记录、Git 清单 |
| `week01-stock-tool/` | 第 1 周：库存台账清洗工具 |
| `week02-schedule/` | 第 2 周：供应商交期台账 |
| `week03-dashboard/` | 第 3 周：库存看板（原生 HTML/CSS/JS） |
| `week04-stock-board/` | 第 4 周：React 版看板 |
| `notes/` | 每周复盘 |

后几周的目录随进度补上。

## 怎么跑

Python 部分：

    uv venv
    uv pip install -r requirements.txt

前端部分：

    cd week04-stock-board
    npm install
    npm run dev

## 进度

- [x] 第 0 周：环境准备
- [ ] 第 1 周：Python 工程化起步
