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

from jstock import StockAPI, quote, kline, bonus, shares


def test_all():
    api = StockAPI()
    print("=" * 50)
    print("股票统一API测试")
    print("=" * 50)

    # 行情
    print("\n📊 行情:")
    for code in ["601398", "600519", "000001"]:
        q = quote(code)
        print(f"  {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")

    # K线
    print("\n📈 K线:")
    for start, end in [("2025-01-01", None), ("2025-01-01", "2025-12-31")]:
        k = api.kline("601398", start=start, end=end)
        print(f"  {start} ~ {end or '今天'}: {len(k.records)} 条")

    # 分红
    print("\n💰 分红:")
    for code in ["601398", "600519"]:
        b = bonus(code)
        print(f"  {b.symbol}: {len(b.records)} 条")
        for r in b.records[:2]:
            print(f"    {r.dividend_year}: {r.plan_explain}")

    # 股本
    print("\n📈 股本:")
    s = shares("601398")
    print(f"  {s.symbol}: {len(s.records)} 条")
    for r in s.records[:2]:
        print(f"    {r.chg_date}: {r.total_shares}")

    print("\n✅ 完成")


if __name__ == "__main__":
    test_all()
