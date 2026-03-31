# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 同花顺接口测试
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from stock.stock_ths import get_daily_kline, daily_kline


def test_daily_kline():
    """测试日K线"""
    print("=" * 50)
    print("测试 日K线")
    print("=" * 50)
    
    # 测试多个股票
    stocks = [
        ("601398", "sh", "工商银行"),
        ("600519", "sh", "贵州茅台"),
        ("000001", "sz", "平安银行"),
    ]
    
    for code, market, name in stocks:
        try:
            kline = get_daily_kline(code, market)
            print(f"✅ {code} ({name}) - 共 {len(kline)} 条数据")
            
            # 显示最近5条
            for record in kline.records[-5:]:
                vol_str = f"{record.volume / 100000000:.2f}亿" if record.volume else "0"
                print(f"   {record.timestamp}: 开={record.open}, 收={record.close}, 高={record.high}, 低={record.low}, 量={vol_str}")
            print()
        except Exception as e:
            print(f"❌ {code} ({name}) 失败: {e}")
            print()


def test_date_range():
    """测试日期范围筛选"""
    print("=" * 50)
    print("测试 日期范围")
    print("=" * 50)
    
    kline = get_daily_kline("601398", "sh")
    
    # 筛选2024年数据
    kline_2024 = [r for r in kline.records if r.timestamp.startswith("2024")]
    print(f"2024年数据: {len(kline_2024)} 条")
    
    if kline_2024:
        print(f"  起始: {kline_2024[0].timestamp}")
        print(f"  结束: {kline_2024[-1].timestamp}")
    print()


def test_all():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 同花顺接口测试")
    print("=" * 60 + "\n")
    
    test_daily_kline()
    test_date_range()
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
