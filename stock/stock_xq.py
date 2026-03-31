# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 雪球API客户端
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import fcntl
import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
from playwright.sync_api import sync_playwright

from stock.config import XUEQIU_TOKEN_FILE, XUEQIU_TOKEN_LOCK
from stock.models import (
    BonusHistory,
    BonusRecord,
    KlineData,
    KlineRecord,
    SharesChangeRecord,
    SharesHistory,
    StockQuote,
)

TOKEN_MAX_AGE = 6 * 60 * 60
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ============ 工具函数 ============
def normalize_symbol(code: str, market: str = None) -> str:
    """规范化股票代码，自动添加 SH/SZ 前缀"""
    code = code.strip()
    
    if len(code) > 6 and code[:2].upper() in ('SH', 'SZ'):
        return code[:2].upper() + code[2:]
    
    code = code.lstrip('SHshSZsz')
    
    if market is None:
        first = code[0] if code else ''
        market = 'SH' if first in ('6', '5', '8') else 'SZ'
    
    return f"{market.upper()}{code}"


def _ts_to_str(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _ts_to_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


# ============ Token管理 ============
def _read_cache():
    if not os.path.exists(XUEQIU_TOKEN_FILE):
        return None, None, False
    try:
        with open(XUEQIU_TOKEN_FILE) as f:
            data = json.load(f)
        token = data.get('token')
        cookie = data.get('cookie_str')
        if time.time() - data.get('timestamp', 0) > TOKEN_MAX_AGE:
            return token, cookie, False
        return token, cookie, data.get('is_valid', True)
    except:
        return None, None, False


def _write_cache(token, cookie):
    try:
        os.makedirs(os.path.dirname(XUEQIU_TOKEN_FILE), exist_ok=True)
        with open(XUEQIU_TOKEN_FILE, 'w') as f:
            json.dump({
                'token': token,
                'cookie_str': cookie,
                'timestamp': time.time(),
                'is_valid': True
            }, f)
    except:
        pass


def _fetch_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        page.goto("https://xueqiu.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        cookies = context.cookies(["https://xueqiu.com"])
        token = None
        parts = []
        for c in cookies:
            if c['name'] == 'xq_a_token':
                token = c['value']
            parts.append(f"{c['name']}={c['value']}")
        return token, '; '.join(parts) if parts else None


def _get_cookies():
    """获取Token（进程安全）"""
    token, cookie, valid = _read_cache()
    if token and cookie and valid:
        return token, cookie
    
    _ensure_dir()
    lock = open(XUEQIU_TOKEN_LOCK, 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        time.sleep(1)
        lock = open(XUEQIU_TOKEN_LOCK, 'w')
        fcntl.flock(lock, fcntl.LOCK_EX)
    
    try:
        token, cookie, valid = _read_cache()
        if token and cookie and valid:
            return token, cookie
        
        token, cookie = _fetch_cookies()
        if token and cookie:
            _write_cache(token, cookie)
        return token, cookie
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def _ensure_dir():
    from stock.config import ensure_dirs
    ensure_dirs()


# ============ 客户端 ============
class XueqiuClient:
    
    def __init__(self, token: str = None, cookie: str = None):
        self.session = requests.Session()
        self.token = token
        self.cookie = cookie
        self._headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://xueqiu.com",
            "Accept": "application/json",
        }
        if not self.token or not self.cookie:
            self._ensure_cookies()

    def _ensure_cookies(self):
        if not self.token or not self.cookie:
            self.token, self.cookie = _get_cookies()

    def _request(self, url, params=None):
        self._ensure_cookies()
        headers = self._headers.copy()
        headers["cookie"] = self.cookie
        resp = self.session.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        
        if data.get('error_code') == 400016:
            self.token, self.cookie = _get_cookies()
            if self.cookie:
                headers["cookie"] = self.cookie
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
                data = resp.json()
        return data

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        """获取股票行情"""
        symbol = normalize_symbol(symbol, market)
        url = f"https://stock.xueqiu.com/v5/stock/quote.json?symbol={symbol}&extend=detail"
        data = self._request(url)
        q = data["data"]["quote"]
        
        return StockQuote(
            name=q.get("name"),
            symbol=q.get("symbol"),
            time=_ts_to_str(int(q["time"])) if q.get("time") else None,
            current=q.get("current"),
            last_close=q.get("last_close"),
            open=q.get("open"),
            high=q.get("high"),
            low=q.get("low"),
            chg=q.get("chg"),
            percent=q.get("percent"),
            volume=q.get("volume"),
            amount=q.get("amount"),
            turnover_rate=q.get("turnover_rate"),
            pe_ttm=q.get("pe_ttm"),
            pe_lyr=q.get("pe_lyr"),
            pe_forecast=q.get("pe_forecast"),
            pb=q.get("pb"),
            dividend_yield=q.get("dividend_yield"),
            eps=q.get("eps"),
            navps=q.get("navps"),
            market_capital=q.get("market_capital"),
            high52w=q.get("high52w"),
            low52w=q.get("low52w"),
        )

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        """获取分红历史"""
        symbol = normalize_symbol(symbol, market)
        url = "https://stock.xueqiu.com/v5/stock/f10/cn/bonus.json"
        data = self._request(url, {"symbol": symbol, "size": "1000", "page": "1", "extend": "true"})
        
        if 'data' not in data or not data['data']:
            return BonusHistory(symbol=symbol, records=[])
        
        records = [
            BonusRecord(
                dividend_year=item.get("dividend_year"),
                equity_date=_ts_to_date(int(item["equity_date"])) if item.get("equity_date") else None,
                ex_dividend_date=_ts_to_date(int(item["ex_dividend_date"])) if item.get("ex_dividend_date") else None,
                dividend_date=_ts_to_date(int(item["dividend_date"])) if item.get("dividend_date") else None,
                plan_explain=item.get("plan_explain"),
            )
            for item in data["data"].get("items", [])
        ]
        return BonusHistory(symbol=symbol, records=records)

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        """获取股本变动"""
        symbol = normalize_symbol(symbol, market)
        url = "https://stock.xueqiu.com/v5/stock/f10/cn/shareschg.json"
        data = self._request(url, {"symbol": symbol, "count": "200", "extend": "true"})
        
        if 'data' not in data or not data['data']:
            return SharesHistory(symbol=symbol, records=[])
        
        records = []
        for item in data["data"].get("items", []):
            total = item.get("total_shares")
            float_a = item.get("float_shares_float_ashare")
            float_h = item.get("float_shares_float_hshare")
            records.append(SharesChangeRecord(
                chg_date=_ts_to_date(int(item["chg_date"])) if item.get("chg_date") else None,
                total_shares=round(total / 100000000, 2) if total else None,
                float_shares_ashare=round(float_a / 100000000, 2) if float_a else None,
                float_shares_hshare=round(float_h / 100000000, 2) if float_h else None,
                chg_reason=item.get("chg_reason"),
            ))
        return SharesHistory(symbol=symbol, records=records)

    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        """获取日K线"""
        symbol = normalize_symbol(symbol, market)
        now = datetime.now()
        
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else now
        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else now - timedelta(days=365)
        
        days = (end_dt - start_dt).days + 1
        count = max(math.ceil(days * 1.2), 2500)
        
        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        data = self._request(url, {
            "symbol": symbol,
            "begin": str(int(end_dt.timestamp() * 1000)),
            "period": "day",
            "type": "before",
            "count": str(-count),
        })
        
        if 'data' not in data or not data['data']:
            return KlineData(symbol=symbol, period="day", records=[])
        
        cols = data["data"].get("column", [])
        items = data["data"].get("item", [])
        if not items:
            return KlineData(symbol=symbol, period="day", records=[])
        
        idx = {col: i for i, col in enumerate(cols)}
        start_date = start_dt.date()
        
        records = [
            KlineRecord(
                timestamp=_ts_to_date(int(item[idx["timestamp"]])) if item[idx.get("timestamp")] else None,
                open=item[idx.get("open")],
                close=item[idx.get("close")],
                high=item[idx.get("high")],
                low=item[idx.get("low")],
                volume=item[idx.get("volume")],
                amount=item[idx.get("amount")],
                turnover=item[idx.get("turnoverrate")],
                chg=item[idx.get("chg")],
                percent=item[idx.get("percent")],
            )
            for item in items
            if datetime.strptime(_ts_to_date(int(item[idx["timestamp"]])), "%Y-%m-%d").date() >= start_date
        ]
        return KlineData(symbol=symbol, period="day", records=records)


# ============ 便捷函数 ============
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = XueqiuClient()
    return _client


def quote(symbol: str, market: str = None) -> StockQuote:
    return _get_client().quote(symbol, market)


def bonus(symbol: str, market: str = None) -> BonusHistory:
    return _get_client().bonus(symbol, market)


def shares(symbol: str, market: str = None) -> SharesHistory:
    return _get_client().shares(symbol, market)


def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    return _get_client().kline(symbol, market, start, end)


# ============ 主程序 ============
if __name__ == "__main__":
    print("=" * 50)
    print("测试雪球API")
    print("=" * 50)
    
    # 行情
    print("\n📊 行情:")
    for code in ["601398", "600519", "000001"]:
        q = quote(code)
        print(f"  {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")
    
    # K线
    print("\n📈 K线:")
    k = kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    for r in k.records[:3]:
        print(f"    {r.timestamp}: {r.close}")
    
    print("\n✅ 完成")
