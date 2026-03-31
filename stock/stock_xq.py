# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/1/13 15:00
Updated: 2026-03-31
Desc: 雪球API客户端 - 自动管理Token
https://xueqiu.com/S/SH601398
"""

# 直接运行时添加项目根目录到路径
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import time
import json
import fcntl
import requests
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright
from stock.models import (
    StockQuote,
    BonusHistory,
    BonusRecord,
    SharesHistory,
    SharesChangeRecord,
    KlineData,
    KlineRecord,
)


from stock.config import XUEQIU_CACHE_DIR, XUEQIU_TOKEN_FILE, XUEQIU_TOKEN_LOCK


# ============ 常量定义 ============
TOKEN_MAX_AGE = 6 * 60 * 60  # Token有效期6小时

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ============ 工具函数 ============
def _ensure_dir():
    """确保目录存在"""
    from stock.config import ensure_dirs
    ensure_dirs()


def _convert_timestamp(timestamp_ms: int) -> str:
    """时间戳转换为字符串时间"""
    timestamp_s = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_s).strftime("%Y-%m-%d %H:%M:%S")


def _convert_date(timestamp_ms: int) -> str:
    """时间戳转换为日期字符串（仅日期）"""
    timestamp_s = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_s).strftime("%Y-%m-%d")


# ============ Token管理 ============
def _read_cache() -> tuple[Optional[str], Optional[str], bool]:
    """
    读取缓存的Token和Cookies，返回 (token, cookie_str, is_valid)
    """
    if not os.path.exists(XUEQIU_TOKEN_FILE):
        return None, None, False

    try:
        with open(XUEQIU_TOKEN_FILE, 'r') as f:
            data = json.load(f)

        token = data.get('token')
        cookie_str = data.get('cookie_str')
        timestamp = data.get('timestamp', 0)
        is_valid = data.get('is_valid', True)

        # 检查是否过期（超过6小时）
        if time.time() - timestamp > TOKEN_MAX_AGE:
            return token, cookie_str, False

        return token, cookie_str, is_valid

    except Exception:
        return None, None, False


def _write_cache(token: str, cookie_str: str = None, is_valid: bool = True):
    """写入Token到缓存"""
    try:
        _ensure_dir()
        with open(XUEQIU_TOKEN_FILE, 'w') as f:
            json.dump({
                'token': token,
                'cookie_str': cookie_str,
                'timestamp': time.time(),
                'is_valid': is_valid
            }, f)
    except Exception:
        pass


def _fetch_cookies() -> tuple[Optional[str], Optional[str]]:
    """
    从浏览器获取Token和完整Cookie
    
    Returns: (xq_a_token, cookie_str)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT
        )
        page = context.new_page()

        page.goto("https://xueqiu.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # 获取所有cookies
        cookies = context.cookies(["https://xueqiu.com"])
        
        token = None
        cookie_parts = []
        for c in cookies:
            if c['name'] == 'xq_a_token':
                token = c['value']
            cookie_parts.append(f"{c['name']}={c['value']}")
        
        cookie_str = '; '.join(cookie_parts) if cookie_parts else None
        
        browser.close()
        
        return token, cookie_str


def _get_token() -> str:
    """获取雪球Token（兼容旧接口）"""
    token, _ = _get_cookies()
    return token


def _get_cookies() -> tuple[str, str]:
    """
    获取雪球Token和完整Cookie（进程安全）
    
    Returns: (xq_a_token, cookie_str)
    
    1. 检查缓存，未过期且有效则直接返回
    2. 使用文件锁防止并发
    3. 双重检查缓存
    4. 获取新Token并缓存
    """
    # 快速路径：直接读缓存
    token, cookie_str, is_valid = _read_cache()
    if token and cookie_str and is_valid:
        return token, cookie_str

    # 加锁
    _ensure_dir()
    lock_fd = open(XUEQIU_TOKEN_LOCK, 'w')

    try:
        # 非阻塞锁，最多等10秒
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

            # 获取新Token和Cookies
            token, cookie_str = _fetch_cookies()
            if token and cookie_str:
                # 写入缓存
                _write_cache(token, cookie_str, is_valid=True)

            return token, cookie_str

        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    except Exception:
        try:
            lock_fd.close()
        except Exception:
            pass
        return None, None


# ============ 雪球客户端类 ============
class XueqiuClient:
    """
    雪球API客户端
    
    自动管理Token，支持：
    - 并发安全（文件锁）
    - Token缓存
    - 自动验证和刷新
    
    返回数据结构（不使用DataFrame）：
    - StockQuote: 单个股票行情数据
    - BonusHistory: 分红历史列表
    - SharesHistory: 股本变动历史列表
    - KlineData: K线数据列表
    
    使用示例：
        client = XueqiuClient()
        
        # 获取股票行情
        quote = client.stock_quote("SH601398")
        print(quote.name, quote.current, quote.pe_ttm)
        
        # 获取分红数据
        bonus = client.stock_bonus("SH601398")
        for record in bonus.records:
            print(record.dividend_year, record.plan_explain)
    """

    def __init__(self, token: str = None, cookie_str: str = None):
        """
        初始化客户端
        
        :param token: 可选，指定Token
        :param cookie_str: 可选，指定完整Cookie
        """
        self.session = requests.Session()
        self.token = token
        self.cookie_str = cookie_str
        self._headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://xueqiu.com",
            "Accept": "application/json",
        }
        
        # 如果没有指定token，则获取
        if not self.token or not self.cookie_str:
            self._ensure_cookies()

    def _ensure_cookies(self):
        """确保有有效的Token和Cookie"""
        if not self.token or not self.cookie_str:
            self.token, self.cookie_str = _get_cookies()

    def _request(self, url: str, params: dict = None) -> dict:
        """
        发起GET请求，自动处理Token失效
        
        :param url: 请求URL
        :param params: URL参数
        :return: JSON响应
        """
        self._ensure_cookies()

        headers = self._headers.copy()
        headers["cookie"] = self.cookie_str

        response = self.session.get(url, params=params, headers=headers, timeout=15)
        data = response.json()

        # Token失效，重试
        if data.get('error_code') == 400016:
            self.token, self.cookie_str = _get_cookies()
            if self.cookie_str:
                headers["cookie"] = self.cookie_str
                response = self.session.get(url, params=params, headers=headers, timeout=15)
                data = response.json()

        return data

    # ============ 公开API ============

    def stock_quote(self, symbol: str) -> StockQuote:
        """
        获取股票行情
        
        :param symbol: 证券代码，如 SH601398
        :return: StockQuote 对象
        """
        url = f"https://stock.xueqiu.com/v5/stock/quote.json?symbol={symbol}&extend=detail"
        json_data = self._request(url)

        quote_data = json_data["data"]["quote"]
        
        # 字段映射关系
        field_map = {
            "name": "name",
            "symbol": "symbol", 
            "time": "time",
            "current": "current",
            "last_close": "last_close",
            "open": "open",
            "high": "high",
            "low": "low",
            "chg": "chg",
            "percent": "percent",
            "volume": "volume",
            "amount": "amount",
            "turnover_rate": "turnover_rate",
            "pe_ttm": "pe_ttm",
            "pe_lyr": "pe_lyr",
            "pe_forecast": "pe_forecast",
            "pb": "pb",
            "dividend_yield": "dividend_yield",
            "eps": "eps",
            "navps": "navps",
            "market_capital": "market_capital",
            "high52w": "high52w",
            "low52w": "low52w",
        }
        
        # 提取数据
        quote_dict = {}
        for attr_name, json_key in field_map.items():
            value = quote_data.get(json_key)
            # 转换时间戳
            if attr_name == "time" and value:
                value = _convert_timestamp(int(value))
            quote_dict[attr_name] = value
        
        return StockQuote(**quote_dict)

    def stock_bonus(self, symbol: str) -> BonusHistory:
        """
        获取分红历史
        
        :param symbol: 证券代码，如 SH601398
        :return: BonusHistory 对象
        """
        url = f"https://stock.xueqiu.com/v5/stock/f10/cn/bonus.json"
        params = {"symbol": symbol, "size": "1000", "page": "1", "extend": "true"}

        json_data = self._request(url, params)
        
        if 'data' not in json_data or not json_data['data']:
            return BonusHistory(symbol=symbol, records=[])
        
        items = json_data["data"].get("items", [])
        
        # 解析每条记录
        records = []
        for item in items:
            record = BonusRecord(
                dividend_year=item.get("dividend_year"),
                equity_date=_convert_date(int(item["equity_date"])) if item.get("equity_date") else None,
                ex_dividend_date=_convert_date(int(item["ex_dividend_date"])) if item.get("ex_dividend_date") else None,
                dividend_date=_convert_date(int(item["dividend_date"])) if item.get("dividend_date") else None,
                plan_explain=item.get("plan_explain"),
            )
            records.append(record)
        
        return BonusHistory(
            symbol=symbol,
            records=records
        )

    def stock_shares(self, symbol: str) -> SharesHistory:
        """
        获取股本变动历史
        
        :param symbol: 证券代码，如 SH601398
        :return: SharesHistory 对象
        """
        url = f"https://stock.xueqiu.com/v5/stock/f10/cn/shareschg.json"
        params = {"symbol": symbol, "count": "200", "extend": "true"}

        json_data = self._request(url, params)

        if 'data' not in json_data or not json_data['data']:
            return SharesHistory(symbol=symbol, records=[])

        items = json_data["data"].get("items", [])
        
        # 解析每条记录
        records = []
        for item in items:
            # 转换股本单位（股 -> 亿股）
            total = item.get("total_shares")
            total_str = f"{total / 100000000:.2f}亿股" if total else None
            
            float_ashare = item.get("float_shares_float_ashare")
            float_ashare_str = f"{float_ashare / 100000000:.2f}亿股" if float_ashare else None
            
            float_hshare = item.get("float_shares_float_hshare")
            float_hshare_str = f"{float_hshare / 100000000:.2f}亿股" if float_hshare else None
            
            record = SharesChangeRecord(
                chg_date=_convert_date(int(item["chg_date"])) if item.get("chg_date") else None,
                total_shares=total_str,
                float_shares_ashare=float_ashare_str,
                float_shares_hshare=float_hshare_str,
                chg_reason=item.get("chg_reason"),
            )
            records.append(record)
        
        return SharesHistory(symbol=symbol, records=records)

    def stock_kline(self, symbol: str, period: str = "day", count: int = -250) -> KlineData:
        """
        获取K线数据
        
        :param symbol: 证券代码，如 SH601398
        :param period: 周期，day/week/month/quarter/year
        :param count: 数据条数，负数向前，正数向后
        :return: KlineData 对象
        """
        from datetime import datetime as dt

        # 设置时间范围
        end = int(dt.now().timestamp() * 1000)

        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        params = {
            "symbol": symbol,
            "begin": str(end),
            "period": period,
            "type": "before",
            "count": str(count),
        }

        json_data = self._request(url, params)

        if 'data' not in json_data or not json_data['data']:
            return KlineData(symbol=symbol, period=period, records=[])

        columns = json_data["data"].get("column", [])
        items = json_data["data"].get("item", [])

        if not items:
            return KlineData(symbol=symbol, period=period, records=[])

        # 字段索引
        col_idx = {col: i for i, col in enumerate(columns)}

        # 解析每条记录
        records = []
        for item in items:
            record = KlineRecord(
                timestamp=_convert_date(int(item[col_idx["timestamp"]])) if item[col_idx.get("timestamp")] else None,
                open=item[col_idx.get("open")],
                close=item[col_idx.get("close")],
                high=item[col_idx.get("high")],
                low=item[col_idx.get("low")],
                volume=item[col_idx.get("volume")],
                amount=item[col_idx.get("amount")],
                turnover=item[col_idx.get("turnoverrate")],
                chg=item[col_idx.get("chg")],
                percent=item[col_idx.get("percent")],
            )
            records.append(record)

        return KlineData(symbol=symbol, period=period, records=records)


# ============ 便捷函数 ============
_client = None


def _get_client() -> XueqiuClient:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = XueqiuClient()
    return _client


def stock_quote(symbol: str) -> StockQuote:
    """获取股票行情"""
    return _get_client().stock_quote(symbol)


def stock_bonus(symbol: str) -> BonusHistory:
    """获取分红历史"""
    return _get_client().stock_bonus(symbol)


def stock_shares(symbol: str) -> SharesHistory:
    """获取股本变动"""
    return _get_client().stock_shares(symbol)


def stock_kline(symbol: str, period: str = "day", count: int = -250) -> KlineData:
    """获取K线数据"""
    return _get_client().stock_kline(symbol, period, count)


# ============ 主程序 ============
if __name__ == "__main__":
    # 测试 XueqiuClient
    print("=" * 60)
    print("测试 XueqiuClient")
    print("=" * 60)

    client = XueqiuClient()

    # 1. 获取股票行情
    print("\n📊 股票行情 (SH601398):")
    quote = client.stock_quote("SH601398")
    print(f"名称: {quote.name}")
    print(f"代码: {quote.symbol}")
    print(f"现价: {quote.current}")
    print(f"涨跌: {quote.chg}")
    print(f"涨幅: {quote.percent}%")
    print(f"市盈率(TTM): {quote.pe_ttm}")
    print(f"市净率: {quote.pb}")
    print(f"总市值: {quote.market_capital}")
    print("\n完整数据字典:")
    for k, v in quote.to_dict().items():
        print(f"  {k}: {v}")

    # 2. 获取分红历史
    print("\n\n💰 分红历史 (SH601398):")
    bonus = client.stock_bonus("SH601398")
    print(f"共 {len(bonus)} 条记录")
    for i, record in enumerate(bonus.records[:5]):
        print(f"  [{i+1}] {record.dividend_year}: {record.plan_explain}")
        print(f"      股权登记日: {record.equity_date}, 除权除息日: {record.ex_dividend_date}, 派息日: {record.dividend_date}")

    # 3. 获取股本变动
    print("\n\n📈 股本变动 (SH601398):")
    shares = client.stock_shares("SH601398")
    print(f"共 {len(shares)} 条记录")
    for i, record in enumerate(shares.records[:5]):
        print(f"  [{i+1}] {record.chg_date}: {record.total_shares} | {record.float_shares_ashare}")
        print(f"      变动原因: {record.chg_reason}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
