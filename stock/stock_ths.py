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

from datetime import datetime
from stock.models import KlineData, KlineRecord

import requests


# ============ 工具函数 ============
def normalize_symbol(code: str, market: str = None) -> tuple:
    """规范化股票代码，返回 (code, market)"""
    code = code.strip().lstrip('SHshSZsz')
    if market is None:
        market = 'sh' if code[0] in ('6', '5', '8') else 'sz'
    return code, market.lower()


# ============ 客户端 ============
class THSClient:
    
    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        """获取日K线"""
        code, market = normalize_symbol(symbol, market)
        out_symbol = f"SH{code}" if market == "sh" else f"SZ{code}"
        
        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else None
        
        # 获取数据
        url = f"https://d.10jqka.com.cn/v6/line/{market}_{code}/01/all.js"
        resp = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://q.10jqka.com.cn/"
        }, timeout=15)
        
        import re
        data = eval(re.search(r'\((.*)\)', resp.text, re.DOTALL).group(1))
        
        dates = data['dates'].split(',')
        price = [int(x) for x in data['price'].split(',')]
        volumn = [int(x) for x in data['volumn'].split(',')]
        
        records = []
        date_idx = 0
        
        for year, count in data['sortYear']:
            for _ in range(count):
                if date_idx >= len(dates):
                    break
                
                date_str = dates[date_idx]
                dt = datetime(year, int(date_str[:2]), int(date_str[2:4]))
                
                # 日期过滤
                if start_dt and dt < start_dt:
                    date_idx += 1
                    continue
                if end_dt and dt > end_dt:
                    date_idx += 1
                    continue
                
                # 解析价格: [low, open-low, high-low, close-low] / 100
                offset = date_idx * 4
                low = price[offset] / 100
                
                records.append(KlineRecord(
                    timestamp=dt.strftime("%Y-%m-%d"),
                    open=round(low + price[offset + 1] / 100, 2),
                    close=round(low + price[offset + 3] / 100, 2),
                    high=round(low + price[offset + 2] / 100, 2),
                    low=round(low, 2),
                    volume=volumn[date_idx],
                    amount=None, turnover=None, chg=None, percent=None,
                ))
                date_idx += 1
        
        return KlineData(symbol=out_symbol, period="day", records=records)


# ============ 便捷函数 ============
_client = None


def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    return THSClient().kline(symbol, market, start, end)


# ============ 主程序 ============
if __name__ == "__main__":
    k = kline("601398", start="2026-01-01", end="2026-03-31")
    print(f"SH601398: {len(k.records)} 条")
    for r in k.records[-5:]:
        print(f"  {r.timestamp}: {r.open:.2f}")
