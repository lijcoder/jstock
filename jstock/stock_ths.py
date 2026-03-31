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

import re
from datetime import datetime

import requests

from jstock.models import KlineData, KlineRecord


# ============ 工具函数 ============
def normalize_symbol(code: str, market: str = None) -> tuple:
    """规范化股票代码"""
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
        
        m = re.search(r'\((\{.*\})\)', resp.text, re.DOTALL)
        data = eval(m.group(1))
        
        dates = data['dates'].split(',')
        price = [int(x) for x in data['price'].split(',')]
        volumn = [int(x) for x in data['volumn'].split(',')]
        
        records = []
        prev_close = None
        date_idx = 0
        
        for year, count in data['sortYear']:
            for _ in range(count):
                if date_idx >= len(dates):
                    break
                
                date_str = dates[date_idx]
                dt = datetime(year, int(date_str[:2]), int(date_str[2:4]))
                
                # 日期过滤
                if start_dt and dt < start_dt:
                    # 仍需计算 prev_close
                    offset = date_idx * 4
                    low = price[offset] / 100
                    close = low + price[offset + 3] / 100
                    prev_close = close
                    date_idx += 1
                    continue
                if end_dt and dt > end_dt:
                    date_idx += 1
                    continue
                
                # 解析价格: [low, open-low, high-low, close-low] / 100
                offset = date_idx * 4
                low = price[offset] / 100
                open_p = low + price[offset + 1] / 100
                high = low + price[offset + 2] / 100
                close = low + price[offset + 3] / 100
                
                # 计算涨跌和涨跌幅
                chg = round(close - prev_close, 2) if prev_close else None
                percent = round((close - prev_close) / prev_close * 100, 2) if prev_close else None
                
                # 成交额估算 = 均价 × 成交量
                amount = round((open_p + close) / 2 * volumn[date_idx], 2)
                
                records.append(KlineRecord(
                    timestamp=dt.strftime("%Y-%m-%d"),
                    open=round(open_p, 2),
                    close=round(close, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    volume=volumn[date_idx],
                    amount=amount,
                    turnover=None,  # 需要流通股本
                    chg=chg,
                    percent=percent,
                ))
                
                prev_close = close
                date_idx += 1
        
        return KlineData(symbol=out_symbol, period="day", records=records)


# ============ 便捷函数 ============
def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    return THSClient().kline(symbol, market, start, end)


# ============ 主程序 ============
if __name__ == "__main__":
    k = kline("601398", start="2026-03-01", end="2026-03-31")
    print(f"SH601398: {len(k.records)} 条")
    print(f"{'日期':<12} {'开盘':>7} {'收盘':>7} {'涨跌':>7} {'涨幅':>8} {'成交额':>10}")
    for r in k.records:
        pct = f"{r.percent:+.2f}%" if r.percent else "N/A"
        amt = f"{r.amount/100000000:.2f}亿" if r.amount else "N/A"
        chg = f"{r.chg:+.2f}" if r.chg else "N/A"
        print(f"{r.timestamp:<12} {r.open:>7.2f} {r.close:>7.2f} {chg:>7} {pct:>8} {amt:>10}")
