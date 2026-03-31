# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票统一API测试
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock import StockAPI, quote, kline, bonus, shares


def test_quote():
    """测试行情接口"""
    print("=" * 50)
    print("测试 行情接口")
    print("=" * 50)

    api = StockAPI()

    # 便捷函数
    print("\n[便捷函数 quote()]")
    for code in ["601398", "600519", "000001"]:
        q = quote(code)
        print(f"  ✅ {q.symbol} ({q.name}): 现价={q.current}, 涨跌={q.percent:+.2f}%")

    # 类方法
    print("\n[类方法 api.quote()]")
    for code in ["601398", "600519"]:
        q = api.quote(code)
        print(f"  ✅ {q.symbol} {q.name}")
        print(f"     现价: {q.current}, 市盈率: {q.pe_ttm}, 市净率: {q.pb}")
        print(f"     成交量: {q.volume / 100000000:.2f}亿, 成交额: {q.amount / 100000000:.2f}亿")


def test_kline():
    """测试K线接口"""
    print("\n" + "=" * 50)
    print("测试 K线接口")
    print("=" * 50)

    api = StockAPI()

    # 日K线
    print("\n[日K线 - 便捷函数]")
    for code in ["601398", "000001"]:
        k = kline(code, count=-5)
        print(f"  ✅ {k.symbol} 最近{len(k.records)}天:")
        for r in k.records:
            vol = f"{r.volume / 100000000:.2f}亿" if r.volume else "0"
            print(f"     {r.timestamp}: 开={r.open}, 收={r.close}, 高={r.high}, 低={r.low}, 量={vol}")

    # 周K线
    print("\n[周K线]")
    k = api.kline("600519", period="week", count=-10)
    print(f"  ✅ {k.symbol} 最近{len(k.records)}周:")
    for r in k.records[-5:]:
        print(f"     {r.timestamp}: 收={r.close} ({r.percent:+.2f}%)")


def test_bonus():
    """测试分红接口"""
    print("\n" + "=" * 50)
    print("测试 分红接口")
    print("=" * 50)

    api = StockAPI()

    for code in ["601398", "600519"]:
        b = bonus(code)
        print(f"\n✅ {b.symbol} - 共 {len(b.records)} 条记录")
        for i, r in enumerate(b.records[:5]):
            print(f"   [{i+1}] {r.dividend_year}: {r.plan_explain}")
            if r.equity_date:
                print(f"       登记日: {r.equity_date}, 除权日: {r.ex_dividend_date}, 派息日: {r.dividend_date}")


def test_shares():
    """测试股本接口"""
    print("\n" + "=" * 50)
    print("测试 股本接口")
    print("=" * 50)

    api = StockAPI()

    for code in ["601398", "600519"]:
        s = shares(code)
        print(f"\n✅ {s.symbol} - 共 {len(s.records)} 条记录")
        for i, r in enumerate(s.records[:5]):
            print(f"   [{i+1}] {r.chg_date}: 总股本={r.total_shares}")
            if r.chg_reason:
                print(f"       原因: {r.chg_reason}")


def test_symbol_formats():
    """测试各种代码格式"""
    print("\n" + "=" * 50)
    print("测试 代码格式")
    print("=" * 50)

    api = StockAPI()

    formats = [
        "601398",     # 纯数字
        "SH601398",   # 大写前缀
        "sh601398",   # 小写前缀
        "000001",     # 深圳纯数字
        "SZ000001",   # 深圳大写前缀
        "sz000001",   # 深圳小写前缀
        "300001",     # 创业板
    ]

    print("\n统一转换为 SH/SZ 格式:")
    for code in formats:
        q = api.quote(code)
        print(f"  {code:12} -> {q.symbol} ({q.name})")


def test_all():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 股票统一API测试")
    print("=" * 60)

    test_symbol_formats()
    test_quote()
    test_kline()
    test_bonus()
    test_shares()

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
