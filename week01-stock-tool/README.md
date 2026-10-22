# stock-tool

把仓库导出的「库存台账.xlsx」清洗成规范 CSV，同时输出一份清洗日志。

## 现状

| 天 | 内容 | 状态 |
| --- | --- | --- |
| Day 1 | 项目骨架 + 虚拟环境 + 能跑起来 | 进行中 |
| Day 2 | 依赖管理（requirements.txt / 锁版本） | 未开始 |
| Day 3 | 读数据 + 自定义异常 | 未开始 |
| Day 4 | 清洗规则 + 清洗日志 | 未开始 |
| Day 5 | 命令行参数 + 分级日志 | 未开始 |

## 怎么跑

首次：

    uv venv
    source .venv/Scripts/activate
    uv pip install -e .

之后每次：

    python -m stock_tool

预期输出三行：版本号、Python 版本、解释器绝对路径。
**解释器路径必须落在 `week01-stock-tool/.venv/` 里**，否则说明你用的不是这个项目的环境。

## 目录

    week01-stock-tool/
    ├── pyproject.toml        项目元信息与依赖（唯一的依赖真相来源）
    ├── README.md             干什么用、怎么跑
    ├── data/
    │   ├── input/            原始数据，只读
    │   └── output/           产物，不进 Git
    └── src/
        └── stock_tool/       包目录，代码全在这里
            ├── __init__.py   标记包 + 版本号
            └── __main__.py   支持 python -m stock_tool

## 为什么多一层 src/

如果代码直接放在项目根目录，在根目录运行 Python 时 `import stock_tool` 会读到**源码目录**，
而不是安装后的包——于是「本地能跑、装到别人机器上找不到模块」。
加了 src/ 之后必须真正安装才能导入，从源头堵掉这个差异。
