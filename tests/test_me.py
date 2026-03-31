# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票统一API测试
"""

if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock import StockAPI, quote, kline, bonus, shares


def test():
    print("\n💰 结果:")
    b = kline("601398")
    print(b)

if __name__ == "__main__":
    test()