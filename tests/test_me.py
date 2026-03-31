# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 同花顺接口测试
"""

if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock.stock_ths import kline


def test_all():
    print("=" * 60)
    print("同花顺接口测试")
    print("=" * 60)

    # K线 + 涨跌
    print("\n📈 K线 (含涨跌):")
    k = kline("601398", start="2025-03-30", end="2026-04-31")
    print(f"  {k.symbol}: {len(k.records)} 条")
    print(f"  {'日期':<12} {'开盘':>7} {'收盘':>7} {'最高':>7} {'最低':>7} {'涨跌':>7} {'涨幅':>8} {'成交量':>10} {'成交额':>10}")
    for r in k.records:
        pct = f"{r.percent:+.2f}%" if r.percent else "N/A"
        chg = f"{r.chg:+.2f}" if r.chg else "N/A"
        amt = f"{r.amount/100000000:.1f}亿" if r.amount else "N/A"
        print(f"  {r.timestamp:<12} {r.open:>7.2f} {r.close:>7.2f} {r.high:>7.2f} {r.low:>7.2f} {chg:>7} {pct:>8} {r.volume:>10} {amt:>10}")
    print("\n✅ 完成")


if __name__ == "__main__":
    test_all()
