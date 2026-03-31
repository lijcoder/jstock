# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 雪球接口测试
"""

if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock.stock_xq import XueqiuClient, _get_cookies, normalize_symbol


def test_all():
    print("=" * 50)
    print("雪球接口测试")
    print("=" * 50)

    # Token
    print("\n🔑 Token:")
    token, cookie = _get_cookies()
    print(f"  {token[:20]}..." if token else "None")

    # 代码规范化
    print("\n📝 代码格式化:")
    for code in ["601398", "SH601398", "000001", "SZ000001"]:
        print(f"  {code:12} -> {normalize_symbol(code)}")

    client = XueqiuClient()

    # 行情
    print("\n📊 行情:")
    for code in ["601398", "600519", "000001"]:
        q = client.quote(code)
        print(f"  {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")

    # K线
    print("\n📈 K线:")
    k = client.kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol}: {len(k.records)} 条")
    for r in k.records[:3]:
        print(f"    {r.timestamp}: {r.close}")

    # 分红
    print("\n💰 分红:")
    b = client.bonus("601398")
    print(f"  {b.symbol}: {len(b.records)} 条")
    for r in b.records[:3]:
        print(f"    {r.dividend_year}: {r.plan_explain}")

    print("\n✅ 完成")


if __name__ == "__main__":
    test_all()
