#!/usr/bin/env python3
"""Redis 配置和连接管理"""

import os
import redis
from dotenv import load_dotenv

load_dotenv()

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

# 创建 Redis 客户端
redis_client = redis.Redis(connection_pool=redis_pool)


def get_redis():
    """获取 Redis 客户端"""
    return redis_client


def test_redis_connection():
    """测试 Redis 连接"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        return False
