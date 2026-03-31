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

from stock.stock_ths import THSClient, kline


def test_all():
    print("=" * 50)
    print("同花顺接口测试")
    print("=" * 50)

    # K线
    print("\n📈 K线:")
    k = kline("601398", start="2026-01-01", end="2026-03-31")
    print(f"  {k.symbol}: {len(k.records)} 条")
    for r in k.records[-5:]:
        print(f"    {r.timestamp}: O={r.open:.2f} H={r.high:.2f} L={r.low:.2f} C={r.close:.2f}")

    # 对比雪球
    print("\n🔍 对比雪球:")
    from stock.stock_xq import kline as xq_kline
    k2 = xq_kline("601398", start="2026-01-01", end="2026-03-31")
    
    # 按日期对比
    ths_dict = {r.timestamp: r for r in k.records}
    match_count = 0
    for r2 in k2.records:
        if r2.timestamp in ths_dict:
            r1 = ths_dict[r2.timestamp]
            diff = abs(r1.open - r2.open)
            ok = "✓" if diff < 0.01 else "✗"
            if diff < 0.01:
                match_count += 1

    print(f"  雪球: {len(k2.records)} 条")
    print(f"  同花顺: {len(k.records)} 条")
    print(f"  日期匹配且价格一致: {match_count} 条")

    # 长期数据
    print("\n📊 长期数据:")
    k3 = kline("601398", start="2023-01-01", end="2025-12-31")
    print(f"  2023-2025: {len(k3.records)} 条")

    print("\n✅ 完成")


if __name__ == "__main__":
    test_all()
