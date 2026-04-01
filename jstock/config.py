# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 统一配置管理
"""

import os
from pathlib import Path

# 统一配置目录
CONFIG_DIR = os.path.expanduser("~/.jstock")

# 子目录
CACHE_DIR = os.path.join(CONFIG_DIR, "cache")
DATA_DIR = os.path.join(CONFIG_DIR, "data")
DB_PATH = os.path.join(CONFIG_DIR, "db", "positions.db")

# 雪球相关
XUEQIU_CACHE_DIR = os.path.join(CACHE_DIR, "xueqiu")
XUEQIU_TOKEN_FILE = os.path.join(XUEQIU_CACHE_DIR, "token")
XUEQIU_TOKEN_LOCK = os.path.join(XUEQIU_CACHE_DIR, ".token.lock")


def ensure_dirs():
    """确保所有目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(XUEQIU_CACHE_DIR, exist_ok=True)


def get_config_dir() -> str:
    """获取配置根目录"""
    return CONFIG_DIR


def get_cache_dir() -> str:
    """获取缓存目录"""
    return CACHE_DIR


def get_data_dir() -> str:
    """获取数据目录"""
    return DATA_DIR


# 初始化目录
ensure_dirs()
