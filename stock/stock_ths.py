# !/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Updated: 2026-03-31
Desc: 同花顺日K线数据获取
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json
import re
from typing import Optional
from stock.models import KlineData, KlineRecord


def get_daily_kline(code: str, market: str = "sh") -> KlineData:
    """
    获取同花顺日K线数据
    
    :param code: 股票代码，如 601398
    :param market: 市场，sh(沪市) 或 sz(深市)
    :return: KlineData 对象
    """
    url = f"https://d.10jqka.com.cn/v6/line/{market}_{code}/01/all.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://q.10jqka.com.cn/"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    json_str = re.search(r'\((.*)\)', response.text, re.DOTALL).group(1)
    data = json.loads(json_str)
    
    return _parse_daily_kline(code, data)


def _parse_daily_kline(symbol: str, data: dict) -> KlineData:
    """
    解析日K数据
    
    :param symbol: 股票代码
    :param data: API返回的原始数据
    :return: KlineData 对象
    """
    sort_year = data.get('sortYear', [])
    all_dates = data.get('dates', '').split(',')
    price_vals = [int(x) for x in data.get('price', '').split(',')]
    volumn_vals = [int(x) for x in data.get('volumn', '').split(',')]
    
    records = []
    date_idx = 0
    
    for year, count in sort_year:
        # 边界处理：dates 数组可能比 sortYear 总数少1
        remaining_dates = len(all_dates) - date_idx
        actual_count = min(count, remaining_dates)
        
        if actual_count <= 0:
            break
        
        year_dates = all_dates[date_idx:date_idx + actual_count]
        date_idx += actual_count
        
        for i in range(actual_count):
            date_str = year_dates[i]
            month = int(date_str[:2])
            day = int(date_str[2:4])
            full_date = f"{year}-{month:02d}-{day:02d}"
            
            offset = len(records) * 4
            # 边界检查
            if offset + 3 >= len(price_vals):
                break
            
            raw_low = price_vals[offset]
            raw_open_diff = price_vals[offset + 1]
            raw_high_diff = price_vals[offset + 2]
            raw_close_diff = price_vals[offset + 3]
            
            low = raw_low / 100
            open_p = low + raw_open_diff / 100
            high = low + raw_high_diff / 100
            close_p = low + raw_close_diff / 100
            
            # 成交量
            volume = volumn_vals[len(records)] if len(records) < len(volumn_vals) else 0
            
            record = KlineRecord(
                timestamp=full_date,
                open=round(open_p, 2),
                close=round(close_p, 2),
                high=round(high, 2),
                low=round(low, 2),
                volume=volume,
                amount=None,
                turnover=None,
                chg=None,
                percent=None,
            )
            records.append(record)
    
    return KlineData(symbol=symbol, period="day", records=records)


# ============ 便捷函数 ============
_client = None


def daily_kline(code: str, market: str = "sh") -> KlineData:
    """获取日K线数据"""
    return get_daily_kline(code, market)


# ============ 主程序 ============
if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("测试 同花顺日K线")
    print("=" * 60)
    
    # 测试沪市
    print("\n📈 日K线 (SH601398):")
    kline = get_daily_kline("601398", "sh")
    print(f"共 {len(kline)} 条记录")
    print(f"{'日期':<12} {'开盘':<10} {'收盘':<10} {'最高':<10} {'最低':<10} {'成交量':<15}")
    print("-" * 70)
    
    # 只显示最近10条
    for record in kline.records[-10:]:
        vol_str = f"{record.volume / 100000000:.2f}亿" if record.volume else "0"
        print(f"{record.timestamp:<12} {record.open:<10.2f} {record.close:<10.2f} {record.high:<10.2f} {record.low:<10.2f} {vol_str}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
