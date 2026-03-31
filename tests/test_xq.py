# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 雪球接口测试
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock.stock_xq import XueqiuClient, _get_cookies, normalize_symbol


def test_token():
    """测试Token获取"""
    print("=" * 50)
    print("测试 Token 获取")
    print("=" * 50)
    
    token, cookie_str = _get_cookies()
    print(f"Token: {token[:20]}..." if token else "None")
    print(f"Cookie长度: {len(cookie_str) if cookie_str else 0}")
    print()


def test_normalize_symbol():
    """测试股票代码规范化"""
    print("=" * 50)
    print("测试 股票代码规范化")
    print("=" * 50)
    
    tests = ["601398", "SH601398", "sh601398", "000001", "SZ000001", "300001"]
    for code in tests:
        print(f"  {code:12} -> {normalize_symbol(code)}")
    print()


def test_stock_quote():
    """测试股票行情"""
    print("=" * 50)
    print("测试 股票行情")
    print("=" * 50)
    
    client = XueqiuClient()
    
    # 支持简化代码
    codes = ["601398", "600519", "000001"]
    
    for code in codes:
        try:
            q = client.stock_quote(code)
            print(f"✅ {q.symbol} ({q.name})")
            print(f"   现价: {q.current}, 涨跌: {q.chg} ({q.percent}%)")
            print(f"   市盈率: {q.pe_ttm}, 市净率: {q.pb}")
            print(f"   成交量: {q.volume / 100000000:.2f}亿")
            print()
        except Exception as e:
            print(f"❌ {code} 失败: {e}\n")


def test_stock_bonus():
    """测试分红历史"""
    print("=" * 50)
    print("测试 分红历史")
    print("=" * 50)
    
    client = XueqiuClient()
    
    for code in ["601398", "600519"]:
        try:
            b = client.stock_bonus(code)
            print(f"✅ {code} - 共 {len(b.records)} 条记录")
            for i, r in enumerate(b.records[:3]):
                print(f"   [{i+1}] {r.dividend_year}: {r.plan_explain}")
            print()
        except Exception as e:
            print(f"❌ {code} 失败: {e}\n")


def test_stock_shares():
    """测试股本变动"""
    print("=" * 50)
    print("测试 股本变动")
    print("=" * 50)
    
    client = XueqiuClient()
    
    for code in ["601398", "600519"]:
        try:
            s = client.stock_shares(code)
            print(f"✅ {code} - 共 {len(s.records)} 条记录")
            for i, r in enumerate(s.records[:3]):
                print(f"   [{i+1}] {r.chg_date}: {r.total_shares}")
            print()
        except Exception as e:
            print(f"❌ {code} 失败: {e}\n")


def test_kline():
    """测试K线接口"""
    print("=" * 50)
    print("测试 K线接口")
    print("=" * 50)
    
    client = XueqiuClient()
    
    for code in ["601398", "000001"]:
        try:
            k = client.stock_kline(code, period="day", count=-5)
            print(f"✅ {code} - 共 {len(k.records)} 条数据")
            for r in k.records:
                vol = f"{r.volume / 100000000:.2f}亿" if r.volume else "0"
                print(f"   {r.timestamp}: 开={r.open}, 收={r.close}, 高={r.high}, 低={r.low}, 量={vol}")
            print()
        except Exception as e:
            print(f"❌ {code} 失败: {e}\n")


def test_all():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 雪球接口测试")
    print("=" * 60 + "\n")
    
    test_token()
    test_normalize_symbol()
    test_stock_quote()
    test_stock_bonus()
    test_stock_shares()
    test_kline()
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
