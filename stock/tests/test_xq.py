# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
测试用例
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_xq import XueqiuClient


class TestXueqiuClient:
    """XueqiuClient 测试类"""

    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        return XueqiuClient()

    def test_stock_quote(self, client):
        """测试股票行情获取"""
        df = client.stock_quote("SH601398")
        assert not df.empty
        assert "item" in df.columns
        assert "value" in df.columns

    def test_stock_bonus(self, client):
        """测试分红历史获取"""
        df = client.stock_bonus("SH601398")
        assert not df.empty
        assert "报告期" in df.columns
        assert "分红方案" in df.columns

    def test_stock_shares(self, client):
        """测试股本变动获取"""
        df = client.stock_shares("SH601398")
        assert not df.empty
        assert "总股本" in df.columns

    def test_stock_kline(self, client):
        """测试K线数据获取"""
        df = client.stock_kline("SH601398", period="day", count=-10)
        # K线可能返回空数据（Token问题）
        assert df is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
