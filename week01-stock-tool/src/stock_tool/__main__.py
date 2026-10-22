"""命令行入口：python -m stock_tool

Day 1 的版本只做一件事——确认「包能装上、能被导入、能跑起来」。
真正的清洗逻辑从 Day 3 开始往里填。
"""

import sys

from stock_tool import __version__


def main() -> int:
    print(f"stock-tool {__version__}")
    print(f"Python  : {sys.version.split()[0]}")
    print(f"解释器  : {sys.executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
