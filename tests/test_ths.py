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

from jstock.stock_ths import kline


def test_all():
    print("=" * 60)
    print("同花顺接口测试")
    print("=" * 60)

    # K线 + 涨跌
    print("\n📈 K线 (含涨跌):")
    k = kline("601398", start="2026-03-01", end="2026-03-31")
    print(f"  {k.symbol}: {len(k.records)} 条")
    print(f"  {'日期':<12} {'收盘':>7} {'涨跌':>7} {'涨幅':>8} {'成交额':>10}")
    for r in k.records[-10:]:
        pct = f"{r.percent:+.2f}%" if r.percent else "N/A"
        chg = f"{r.chg:+.2f}" if r.chg else "N/A"
        amt = f"{r.amount/100000000:.1f}亿" if r.amount else "N/A"
        print(f"  {r.timestamp:<12} {r.close:>7.2f} {chg:>7} {pct:>8} {amt:>10}")

    # 对比雪球
    print("\n🔍 对比雪球:")
    from jstock.stock_xq import kline as xq_kline
    xq = xq_kline("601398", start="2026-03-01", end="2026-03-31")
    
    ths_dict = {r.timestamp: r for r in k.records}
    match = 0
    for r in xq.records:
        if r.timestamp in ths_dict:
            t = ths_dict[r.timestamp]
            if abs((t.percent or 0) - r.percent) < 0.1:
                match += 1
    print(f"  雪球: {len(xq.records)} 条, 同花顺: {len(k.records)} 条, 涨幅一致: {match} 条")

    # 长期数据
    print("\n📊 长期数据 (2023-2025):")
    k2 = kline("601398", start="2023-01-01", end="2025-12-31")
    print(f"  共 {len(k2.records)} 条")

    print("\n✅ 完成")


if __name__ == "__main__":
    test_all()
