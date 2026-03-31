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

import time
import json
from datetime import datetime as dt

from stock.stock_xq import XueqiuClient, _get_cookies, _get_token


def test_token():
    """测试Token获取"""
    print("=" * 50)
    print("测试 Token 获取")
    print("=" * 50)
    
    # 测试 _get_token
    token = _get_token()
    print(f"Token: {token[:20]}..." if token else "None")
    
    # 测试 _get_cookies
    token, cookie_str = _get_cookies()
    print(f"Token: {token[:20]}..." if token else "None")
    print(f"Cookie长度: {len(cookie_str) if cookie_str else 0}")
    
    print()


def test_client_init():
    """测试客户端初始化"""
    print("=" * 50)
    print("测试客户端初始化")
    print("=" * 50)
    
    # 默认初始化
    client = XueqiuClient()
    print(f"Token: {client.token[:20] if client.token else 'None'}...")
    print(f"Cookie长度: {len(client.cookie_str) if client.cookie_str else 0}")
    print(f"Headers: {list(client._headers.keys())}")
    print()


def test_stock_quote():
    """测试股票行情"""
    print("=" * 50)
    print("测试 股票行情")
    print("=" * 50)
    
    client = XueqiuClient()
    
    # 测试多个股票
    symbols = ["SH601398", "SH600519", "SZ000001"]
    
    for symbol in symbols:
        try:
            quote = client.stock_quote(symbol)
            print(f"✅ {symbol} ({quote.name})")
            print(f"   现价: {quote.current}, 涨跌: {quote.chg} ({quote.percent}%)")
            print(f"   市盈率: {quote.pe_ttm}, 市净率: {quote.pb}")
            print(f"   成交量: {quote.volume / 100000000:.2f}亿")
            print()
        except Exception as e:
            print(f"❌ {symbol} 失败: {e}")
            print()


def test_stock_bonus():
    """测试分红历史"""
    print("=" * 50)
    print("测试 分红历史")
    print("=" * 50)
    
    client = XueqiuClient()
    
    # 测试多个股票
    symbols = ["SH601398", "SH600519"]
    
    for symbol in symbols:
        try:
            bonus = client.stock_bonus(symbol)
            print(f"✅ {symbol} - 共 {len(bonus)} 条记录")
            for i, record in enumerate(bonus.records[:3]):
                print(f"   [{i+1}] {record.dividend_year}: {record.plan_explain}")
            print()
        except Exception as e:
            print(f"❌ {symbol} 失败: {e}")
            print()


def test_stock_shares():
    """测试股本变动"""
    print("=" * 50)
    print("测试 股本变动")
    print("=" * 50)
    
    client = XueqiuClient()
    
    # 测试多个股票
    symbols = ["SH601398", "SH600519"]
    
    for symbol in symbols:
        try:
            shares = client.stock_shares(symbol)
            print(f"✅ {symbol} - 共 {len(shares)} 条记录")
            for i, record in enumerate(shares.records[:3]):
                print(f"   [{i+1}] {record.chg_date}: {record.total_shares}")
                print(f"       变动原因: {record.chg_reason}")
            print()
        except Exception as e:
            print(f"❌ {symbol} 失败: {e}")
            print()


def test_kline():
    """测试K线接口"""
    print("=" * 50)
    print("测试 K线接口")
    print("=" * 50)
    
    client = XueqiuClient()
    
    # 测试多个股票
    symbols = ["SH601398", "SH600519", "SZ000001"]
    
    for symbol in symbols:
        try:
            kline = client.stock_kline(symbol, period="day", count=-5)
            print(f"✅ {symbol} - 共 {len(kline)} 条数据")
            for r in kline.records:
                vol_str = f"{r.volume / 100000000:.2f}亿" if r.volume else "0"
                print(f"   {r.timestamp}: 开={r.open}, 收={r.close}, 高={r.high}, 低={r.low}, 量={vol_str}")
            print()
        except Exception as e:
            print(f"❌ {symbol} 失败: {e}")
            print()


def test_all():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 雪球接口测试")
    print("=" * 60 + "\n")
    
    test_token()
    test_client_init()
    test_stock_quote()
    test_stock_bonus()
    test_stock_shares()
    test_kline()
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
