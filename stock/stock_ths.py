# !/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 同花顺API客户端
"""

if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import math
import re
from datetime import datetime

import requests

from stock.models import KlineData, KlineRecord


# ============ 工具函数 ============
def normalize_symbol(code: str, market: str = None) -> tuple:
    """规范化股票代码，返回 (thsh, market)"""
    code = code.strip()
    
    # 已有前缀
    if len(code) > 6 and code[:2].upper() in ('SH', 'SZ'):
        code = code[2:]
    
    code = code.lstrip('SHshSZsz')
    
    if market is None:
        market = 'sh' if code[0] in ('6', '5', '8') else 'sz'
    
    return code, market.lower()


def _fetch_data(code: str, market: str) -> dict:
    """获取K线原始数据"""
    url = f"https://d.10jqka.com.cn/v6/line/{market}_{code}/01/all.js"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://q.10jqka.com.cn/"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    json_str = re.search(r'\((.*)\)', resp.text, re.DOTALL).group(1)
    return eval(json_str)  # 已知是标准 dict，直接 eval


def _parse_kline(symbol: str, data: dict, start: datetime = None, end: datetime = None) -> KlineData:
    """解析K线数据
    
    数据格式：
    - dates: MMDD 格式，按年拼接
    - price: [low, open-low, high-low, close-low]，除以100
    - volumn: 成交量
    - sortYear: [[year, count], ...]
    """
    dates = data['dates'].split(',')
    price = [int(x) for x in data['price'].split(',')]
    volumn = [int(x) for x in data['volumn'].split(',')]
    sort_year = data['sortYear']
    
    records = []
    date_idx = 0
    
    for year, count in sort_year:
        for i in range(count):
            if date_idx >= len(dates):
                break
            
            # 解析日期
            date_str = dates[date_idx]
            month = int(date_str[:2])
            day = int(date_str[2:4])
            dt = datetime(year, month, day)
            
            # 日期过滤
            if start and dt < start:
                date_idx += 1
                continue
            if end and dt > end:
                date_idx += 1
                continue
            
            # 解析价格
            offset = date_idx * 4
            low = price[offset] / 100
            open_p = low + price[offset + 1] / 100
            high = low + price[offset + 2] / 100
            close_p = low + price[offset + 3] / 100
            
            records.append(KlineRecord(
                timestamp=dt.strftime("%Y-%m-%d"),
                open=round(open_p, 2),
                close=round(close_p, 2),
                high=round(high, 2),
                low=round(low, 2),
                volume=volumn[date_idx],
                amount=None,
                turnover=None,
                chg=None,
                percent=None,
            ))
            
            date_idx += 1
    
    return KlineData(symbol=symbol, period="day", records=records)


# ============ 客户端 ============
class THSClient:
    
    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        """获取日K线
        
        :param symbol: 股票代码
        :param market: 市场 sh/sz
        :param start: 开始日期 YYYY-MM-DD
        :param end: 结束日期 YYYY-MM-DD
        """
        code, market = normalize_symbol(symbol, market)
        symbol = f"SH{code}" if market == "sh" else f"SZ{code}"
        
        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else None
        
        data = _fetch_data(code, market)
        return _parse_kline(symbol, data, start_dt, end_dt)
    
    def quote(self, symbol: str, market: str = None):
        """暂不支持"""
        raise NotImplementedError("THS 暂不支持实时行情")
    
    def bonus(self, symbol: str, market: str = None):
        """暂不支持"""
        raise NotImplementedError("THS 暂不支持分红数据")
    
    def shares(self, symbol: str, market: str = None):
        """暂不支持"""
        raise NotImplementedError("THS 暂不支持股本数据")


# ============ 便捷函数 ============
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = THSClient()
    return _client


def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    return _get_client().kline(symbol, market, start, end)


# ============ 主程序 ============
if __name__ == "__main__":
    print("=" * 50)
    print("同花顺K线测试")
    print("=" * 50)
    
    # 完整历史
    k = kline("601398", start="2026-01-01", end="2026-03-31")
    print(f"\n{k.symbol}: {len(k.records)} 条")
    for r in k.records[-5:]:
        print(f"  {r.timestamp}: O={r.open:.2f} H={r.high:.2f} L={r.low:.2f} C={r.close:.2f}")
    
    # 对比雪球
    print("\n对比雪球:")
    from stock.stock_xq import kline as xq_kline
    k2 = xq_kline("601398", start="2026-01-01", end="2026-03-31")
    print(f"雪球: {len(k2.records)} 条")
    for r in k2.records[-3:]:
        print(f"  {r.timestamp}: O={r.open:.2f} H={r.high:.2f} L={r.low:.2f} C={r.close:.2f}")
    
    print("\n✅ 完成")
