# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 雪球API客户端 - 自动管理Token
https://xueqiu.com/S/SH601398
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import fcntl
import json
import os
import time
from datetime import datetime

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

# ============ 常量 ============
TOKEN_MAX_AGE = 6 * 60 * 60  # Token有效期6小时

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ============ 工具函数 ============
def _ensure_dir():
    """确保目录存在"""
    from stock.config import ensure_dirs
    ensure_dirs()


def normalize_symbol(code: str, market: str = None) -> str:
    """
    规范化股票代码，自动添加市场前缀
    
    :param code: 股票代码，支持 601398、SH601398、sh601398 等格式
    :param market: 指定市场，可选 'SH'/'SZ'，如果为 None 则自动判断
    :return: 带前缀的代码，如 'SH601398'
    """
    code = code.strip()
    
    # 已有前缀，直接返回大写
    if len(code) > 6 and code[:2].upper() in ('SH', 'SZ'):
        return code[:2].upper() + code[2:]
    
    # 去除已有前缀
    code = code.lstrip('SHshSZsz')
    
    # 自动判断市场
    if market is None:
        first = code[0] if code else ''
        market = 'SH' if first in ('6', '5', '8') else 'SZ'
    
    return f"{market.upper()}{code}"


def _ts_to_str(timestamp_ms: int) -> str:
    """时间戳 -> YYYY-MM-DD HH:MM:SS"""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _ts_to_date(timestamp_ms: int) -> str:
    """时间戳 -> YYYY-MM-DD"""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")


# ============ Token管理 ============
def _read_cache() -> tuple[str | None, str | None, bool]:
    """读取缓存的Token和Cookies"""
    if not os.path.exists(XUEQIU_TOKEN_FILE):
        return None, None, False

    try:
        with open(XUEQIU_TOKEN_FILE) as f:
            data = json.load(f)

        token = data.get('token')
        cookie_str = data.get('cookie_str')
        timestamp = data.get('timestamp', 0)
        is_valid = data.get('is_valid', True)

        if time.time() - timestamp > TOKEN_MAX_AGE:
            return token, cookie_str, False

        return token, cookie_str, is_valid
    except Exception:
        return None, None, False


def _write_cache(token: str, cookie_str: str = None):
    """写入Token到缓存"""
    try:
        _ensure_dir()
        with open(XUEQIU_TOKEN_FILE, 'w') as f:
            json.dump({
                'token': token,
                'cookie_str': cookie_str,
                'timestamp': time.time(),
                'is_valid': True
            }, f)
    except Exception:
        pass


def _fetch_cookies() -> tuple[str | None, str | None]:
    """从浏览器获取Token和完整Cookie"""
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


def _get_cookies() -> tuple[str, str]:
    """
    获取雪球Token和完整Cookie（进程安全）
    
    1. 检查缓存，未过期且有效则直接返回
    2. 使用文件锁防止并发
    3. 双重检查缓存
    4. 获取新Token并缓存
    """
    # 快速路径
    token, cookie_str, is_valid = _read_cache()
    if token and cookie_str and is_valid:
        return token, cookie_str

    # 加锁
    _ensure_dir()
    lock_fd = open(XUEQIU_TOKEN_LOCK, 'w')

    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_fd.close()
            time.sleep(1)
            lock_fd = open(XUEQIU_TOKEN_LOCK, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

        try:
            # 双重检查
            token, cookie_str, is_valid = _read_cache()
            if token and cookie_str and is_valid:
                return token, cookie_str

            # 获取新Token
            token, cookie_str = _fetch_cookies()
            if token and cookie_str:
                _write_cache(token, cookie_str)

            return token, cookie_str
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        lock_fd.close()


# ============ 客户端 ============
class XueqiuClient:
    """雪球API客户端，自动管理Token"""

    def __init__(self, token: str = None, cookie_str: str = None):
        self.session = requests.Session()
        self.token = token
        self.cookie_str = cookie_str
        self._headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://xueqiu.com",
            "Accept": "application/json",
        }
        
        if not self.token or not self.cookie_str:
            self._ensure_cookies()

    def _ensure_cookies(self):
        if not self.token or not self.cookie_str:
            self.token, self.cookie_str = _get_cookies()

    def _request(self, url: str, params: dict = None) -> dict:
        """发起GET请求，自动处理Token失效"""
        self._ensure_cookies()
        headers = self._headers.copy()
        headers["cookie"] = self.cookie_str

        resp = self.session.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()

        # Token失效，重试
        if data.get('error_code') == 400016:
            self.token, self.cookie_str = _get_cookies()
            if self.cookie_str:
                headers["cookie"] = self.cookie_str
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
                data = resp.json()

        return data

    def stock_quote(self, symbol: str, market: str = None) -> StockQuote:
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

    def stock_bonus(self, symbol: str, market: str = None) -> BonusHistory:
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

    def stock_shares(self, symbol: str, market: str = None) -> SharesHistory:
        """获取股本变动历史"""
        symbol = normalize_symbol(symbol, market)
        url = "https://stock.xueqiu.com/v5/stock/f10/cn/shareschg.json"
        data = self._request(url, {"symbol": symbol, "count": "200", "extend": "true"})

        if 'data' not in data or not data['data']:
            return SharesHistory(symbol=symbol, records=[])

        records = []
        for item in data["data"].get("items", []):
            total = item.get("total_shares")
            total_str = f"{total / 100000000:.2f}亿股" if total else None
            float_a = item.get("float_shares_float_ashare")
            float_a_str = f"{float_a / 100000000:.2f}亿股" if float_a else None
            float_h = item.get("float_shares_float_hshare")
            float_h_str = f"{float_h / 100000000:.2f}亿股" if float_h else None

            records.append(SharesChangeRecord(
                chg_date=_ts_to_date(int(item["chg_date"])) if item.get("chg_date") else None,
                total_shares=total_str,
                float_shares_ashare=float_a_str,
                float_shares_hshare=float_h_str,
                chg_reason=item.get("chg_reason"),
            ))

        return SharesHistory(symbol=symbol, records=records)

    def kline(
        self,
        symbol: str,
        period: str = "day",
        years: float = 5,
        start: str = None,
        end: str = None,
    ) -> KlineData:
        """
        获取K线数据
        
        :param symbol: 股票代码（已规范化）
        :param period: 周期，day/week/month/quarter/year
        :param years: 最近N年（支持小数）
        :param start: 开始日期 YYYY-MM-DD
        :param end: 结束日期 YYYY-MM-DD
        """
        from datetime import datetime, timedelta
        import math
        
        end_ts = int(datetime.now().timestamp() * 1000)
        
        # 根据日期范围计算count
        count = None
        start_ts = None
        
        if start or end:
            # 使用日期范围
            start_dt = datetime.strptime(start, "%Y-%m-%d") if start else datetime.now() - timedelta(days=365 * years)
            end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.now()
            
            # 计算天数
            days = (end_dt - start_dt).days + 1
            if period == "day":
                count = -math.ceil(days * 1.2)  # 多取20%防止周末问题
            elif period == "week":
                count = -math.ceil(days / 7 * 1.2)
            elif period == "month":
                count = -math.ceil(days / 30 * 1.2)
            else:
                count = -math.ceil(days * 1.2)
            
            count = max(count, -2500)  # 最多取2500条
            start_ts = int(start_dt.timestamp() * 1000)
        elif years:
            # 使用年数
            days = int(years * 365)
            if period == "day":
                count = -math.ceil(days * 1.2)
            elif period == "week":
                count = -math.ceil(days / 7 * 1.2)
            elif period == "month":
                count = -math.ceil(days / 30 * 1.2)
            elif period == "quarter":
                count = -math.ceil(days / 91 * 1.2)
            else:
                count = -math.ceil(days * 1.2)
            
            count = max(count, -2500)  # 最多取2500条
        else:
            # 默认5年
            count = -1250

        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        params = {
            "symbol": symbol,
            "begin": str(end_ts),
            "period": period,
            "type": "before",
            "count": str(count),
        }

        data = self._request(url, params)

        if 'data' not in data or not data['data']:
            return KlineData(symbol=symbol, period=period, records=[])

        cols = data["data"].get("column", [])
        items = data["data"].get("item", [])
        if not items:
            return KlineData(symbol=symbol, period=period, records=[])

        idx = {col: i for i, col in enumerate(cols)}

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
        ]

        # 按日期过滤
        if start_ts:
            start_date = datetime.fromtimestamp(start_ts / 1000).date()
            records = [r for r in records if r.timestamp and datetime.strptime(r.timestamp, "%Y-%m-%d").date() >= start_date]

        return KlineData(symbol=symbol, period=period, records=records)


# ============ 便捷函数 ============
_client = None


def _get_client() -> XueqiuClient:
    global _client
    if _client is None:
        _client = XueqiuClient()
    return _client


def stock_quote(symbol: str, market: str = None) -> StockQuote:
    return _get_client().stock_quote(symbol, market)


def stock_bonus(symbol: str, market: str = None) -> BonusHistory:
    return _get_client().stock_bonus(symbol, market)


def stock_shares(symbol: str, market: str = None) -> SharesHistory:
    return _get_client().stock_shares(symbol, market)


def kline(symbol: str, period: str = "day", years: int = 5, start: str = None, end: str = None, market: str = None) -> KlineData:
    """获取K线数据"""
    symbol = normalize_symbol(symbol, market)
    return _get_client().kline(symbol, period, years, start, end)


# ============ 主程序 ============
if __name__ == "__main__":
    client = XueqiuClient()

    print("=" * 50)
    print("测试雪球API")
    print("=" * 50)

    # 股票行情
    print("\n📊 股票行情:")
    for code in ["601398", "600519", "000001"]:
        q = client.stock_quote(code)
        print(f"  {q.symbol} {q.name}: 现价={q.current}, 涨跌={q.chg}({q.percent}%)")

    # 分红历史
    print("\n💰 分红历史:")
    b = client.stock_bonus("601398")
    print(f"  共 {len(b.records)} 条")
    for r in b.records[:3]:
        print(f"  {r.dividend_year}: {r.plan_explain}")

    print("\n✅ 完成")
