# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API - 门面模式
自动选择数据源，调用方无需关心底层实现
"""

from stock import models
from stock.stock_xq import XueqiuClient
from stock.stock_ths import daily_kline as ths_daily_kline

# 导出统一的数据模型
__all__ = [
    'quote',
    'kline',
    'bonus',
    'shares',
    'StockAPI',
]
StockQuote = models.StockQuote
BonusHistory = models.BonusHistory
SharesHistory = models.SharesHistory
KlineData = models.KlineData


# ============ 便捷函数 ============
_quote_client = None
_api_client = None


def _get_quote_client() -> XueqiuClient:
    """获取行情客户端（延迟初始化）"""
    global _quote_client
    if _quote_client is None:
        _quote_client = XueqiuClient()
    return _quote_client


def _get_api() -> 'StockAPI':
    """获取StockAPI实例"""
    global _api_client
    if _api_client is None:
        _api_client = StockAPI()
    return _api_client


def quote(symbol: str, market: str = None) -> StockQuote:
    """
    获取股票行情
    
    :param symbol: 股票代码，支持 601398、SH601398 等格式
    :param market: 指定市场，可选 'SH'/'SZ'
    :return: StockQuote 对象
    """
    return _get_api().quote(symbol, market)


def kline(symbol: str, market: str = None, period: str = "day", count: int = -250) -> KlineData:
    """
    获取K线数据
    
    :param symbol: 股票代码
    :param market: 指定市场
    :param period: 周期，day/week/month/quarter/year
    :param count: 数量，负数向前
    :return: KlineData 对象
    """
    return _get_api().kline(symbol, market, period, count)


def bonus(symbol: str, market: str = None) -> BonusHistory:
    """
    获取分红历史
    
    :param symbol: 股票代码
    :param market: 指定市场
    :return: BonusHistory 对象
    """
    return _get_api().bonus(symbol, market)


def shares(symbol: str, market: str = None) -> SharesHistory:
    """
    获取股本变动
    
    :param symbol: 股票代码
    :param market: 指定市场
    :return: SharesHistory 对象
    """
    return _get_api().shares(symbol, market)


# ============ 主类 ============
class StockAPI:
    """
    股票数据统一API - 门面类
    
    自动选择最优数据源，调用方无需关心底层实现。
    优先使用雪球数据，失败时切换到其他数据源。
    
    使用示例：
        from stock import StockAPI
        
        api = StockAPI()
        
        # 获取行情
        q = api.quote("601398")
        print(q.name, q.current)
        
        # 获取K线
        k = api.kline("601398", period="day", count=-100)
        for r in k.records:
            print(r.date, r.close)
        
        # 便捷函数
        from stock import quote, kline
        q = quote("601398")
        k = kline("601398")
    """

    def __init__(self, primary: str = "xq"):
        """
        初始化
        
        :param primary: 首选数据源，"xq" 或 "ths"
        """
        self.primary = primary
        self._xq_client = None

    @property
    def xq(self) -> XueqiuClient:
        """雪球客户端（延迟初始化）"""
        if self._xq_client is None:
            self._xq_client = XueqiuClient()
        return self._xq_client

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        """
        获取股票行情
        
        :param symbol: 股票代码，支持 601398、SH601398 等格式
        :param market: 指定市场，可选 'SH'/'SZ'
        :return: StockQuote 对象
        """
        try:
            return self.xq.stock_quote(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取行情失败: {e}")

    def kline(
        self,
        symbol: str,
        market: str = None,
        period: str = "day",
        count: int = -250
    ) -> KlineData:
        """
        获取K线数据
        
        :param symbol: 股票代码
        :param market: 指定市场
        :param period: 周期，day/week/month/quarter/year
        :param count: 数量，负数向前，正数向后
        :return: KlineData 对象
        
        注意：THS仅支持日K线
        """
        # 规范化代码
        if market:
            market = market.upper()
        
        # 自动判断市场
        if market is None:
            code = symbol.strip().lstrip('SHshSZsz')
            first = code[0] if code else ''
            market = 'SH' if first in ('6', '5', '8') else 'SZ'
        
        if self.primary == "xq":
            # 优先雪球
            try:
                return self.xq.stock_kline(symbol, market, period, count)
            except Exception:
                pass
        
        # Fallback 到同花顺（仅支持日K）
        if period != "day":
            raise ValueError("THS仅支持日K线，请使用雪球获取其他周期K线")
        
        try:
            market_prefix = "sh" if market == "SH" else "sz"
            return ths_daily_kline(symbol, market_prefix)
        except Exception as e:
            raise RuntimeError(f"获取K线失败: {e}")

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        """
        获取分红历史
        
        :param symbol: 股票代码
        :param market: 指定市场
        :return: BonusHistory 对象
        """
        try:
            return self.xq.stock_bonus(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取分红历史失败: {e}")

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        """
        获取股本变动
        
        :param symbol: 股票代码
        :param market: 指定市场
        :return: SharesHistory 对象
        """
        try:
            return self.xq.stock_shares(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取股本变动失败: {e}")


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()

    print("=" * 50)
    print("测试股票统一API")
    print("=" * 50)

    # 行情
    print("\n📊 股票行情:")
    for code in ["601398", "600519", "000001"]:
        q = api.quote(code)
        print(f"  {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")

    # K线
    print("\n📈 K线数据:")
    k = api.kline("601398", count=-5)
    print(f"  {k.symbol} 最近5个交易日:")
    for r in k.records:
        print(f"    {r.timestamp}: {r.open} -> {r.close} ({r.percent:+.2f}%)")

    # 分红
    print("\n💰 分红历史:")
    b = api.bonus("601398")
    print(f"  {b.symbol} 最近3次分红:")
    for r in b.records[:3]:
        print(f"    {r.dividend_year}: {r.plan_explain}")

    print("\n✅ 完成")
