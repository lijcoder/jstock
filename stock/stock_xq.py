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
)


# ============ 常量定义 ============
CACHE_DIR = os.path.expanduser("~/.cache/xq_stock")
CACHE_FILE = os.path.join(CACHE_DIR, "xq_token")
LOCK_FILE = os.path.join(CACHE_DIR, ".token.lock")
TOKEN_MAX_AGE = 6 * 60 * 60  # Token有效期6小时

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ============ 工具函数 ============
def _ensure_dir():
    """确保目录存在"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _convert_timestamp(timestamp_ms: int) -> str:
    """时间戳转换为字符串时间"""
    timestamp_s = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_s).strftime("%Y-%m-%d %H:%M:%S")


def _convert_date(timestamp_ms: int) -> str:
    """时间戳转换为日期字符串（仅日期）"""
    timestamp_s = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_s).strftime("%Y-%m-%d")


# ============ Token管理 ============
def _read_cache() -> tuple[Optional[str], bool]:
    """
    读取缓存的Token，返回 (token, is_valid)
    """
    if not os.path.exists(CACHE_FILE):
        return None, False

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)

        token = data.get('token')
        timestamp = data.get('timestamp', 0)
        is_valid = data.get('is_valid', True)

        # 检查是否过期（超过6小时）
        if time.time() - timestamp > TOKEN_MAX_AGE:
            return token, False

        return token, is_valid

    except Exception:
        return None, False


def _write_cache(token: str, is_valid: bool = True):
    """写入Token到缓存"""
    try:
        _ensure_dir()
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'token': token,
                'timestamp': time.time(),
                'is_valid': is_valid
            }, f)
    except Exception:
        pass


def _fetch_token() -> Optional[str]:
    """从浏览器获取Token"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://xueqiu.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        cookies = page.context.cookies(["https://xueqiu.com"])
        for c in cookies:
            if c['name'] == 'xq_a_token':
                return c['value']
        return None


def _get_token() -> str:
    """
    获取雪球Token（进程安全）
    
    1. 检查缓存，未过期且有效则直接返回
    2. 使用文件锁防止并发
    3. 双重检查缓存
    4. 获取新Token并缓存
    """
    # 快速路径：直接读缓存
    token, is_valid = _read_cache()
    if token and is_valid:
        return token

    # 加锁
    _ensure_dir()
    lock_fd = open(LOCK_FILE, 'w')

    try:
        # 非阻塞锁，最多等10秒
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_fd.close()
            time.sleep(1)
            lock_fd = open(LOCK_FILE, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

        try:
            # 双重检查
            token, is_valid = _read_cache()
            if token and is_valid:
                return token

            # 获取新Token
            token = _fetch_token()
            if token:
                # 写入缓存
                _write_cache(token, is_valid=True)

            return token

        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    except Exception:
        try:
            lock_fd.close()
        except Exception:
            pass
        return None


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
        
        # 获取K线数据
        kline = client.stock_kline("SH601398", period="day", count=-30)
        for record in kline.records:
            print(record.timestamp, record.close)
    """

    def __init__(self, token: str = None):
        """
        初始化客户端
        
        :param token: 可选，指定Token；默认自动获取
        """
        self.session = requests.Session()
        self.token = token
        self._headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://xueqiu.com",
            "Accept": "application/json",
        }
        
        # 如果没有指定token，则获取
        if not self.token:
            self._ensure_token()

    def _ensure_token(self):
        """确保有有效的Token"""
        if not self.token:
            self.token = _get_token()

    def _verify_token(self, token: str) -> bool:
        """验证Token是否有效"""
        headers = self._headers.copy()
        headers["cookie"] = f"xq_a_token={token};"

        try:
            response = self.session.get(
                "https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH601398",
                headers=headers, timeout=10
            )
            data = response.json()
            return data.get("error_code") == 0
        except Exception:
            return False

    def _request(self, url: str, params: dict = None) -> dict:
        """
        发起GET请求，自动处理Token失效
        
        :param url: 请求URL
        :param params: URL参数
        :return: JSON响应
        """
        self._ensure_token()

        headers = self._headers.copy()
        headers["cookie"] = f"xq_a_token={self.token};"

        response = self.session.get(url, params=params, headers=headers, timeout=15)
        data = response.json()

        # Token失效，重试
        if data.get('error_code') == 400016:
            self.token = _get_token()
            if self.token:
                headers["cookie"] = f"xq_a_token={self.token};"
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
