#!/usr/bin/env python3
"""Redis 单元测试"""

import pytest
from app.core.redis import get_redis, test_redis_connection


def test_redis_connection():
    """测试 Redis 连接"""
    from app.core.redis import test_redis_connection as redis_test
    # 测试连接是否成功
    is_connected = redis_test()
    assert is_connected, "Redis 连接失败"


def test_redis_basic_operations():
    """测试 Redis 基本操作"""
    redis_client = get_redis()
    
    # 测试设置和获取值
    test_key = "test:key"
    test_value = "test_value"
    
    # 设置值
    redis_client.set(test_key, test_value)
    
    # 获取值
    retrieved_value = redis_client.get(test_key)
    assert retrieved_value == test_value, "Redis 设置和获取失败"
    
    # 测试删除
    redis_client.delete(test_key)
    assert redis_client.get(test_key) is None, "Redis 删除失败"


def test_redis_hash_operations():
    """测试 Redis Hash 操作"""
    redis_client = get_redis()
    
    # 测试设置和获取哈希值
    test_hash = "test:hash"
    
    # 设置哈希字段
    redis_client.hset(test_hash, "field1", "value1")
    redis_client.hset(test_hash, "field2", "value2")
    
    # 获取哈希字段
    field1_value = redis_client.hget(test_hash, "field1")
    field2_value = redis_client.hget(test_hash, "field2")
    assert field1_value == "value1", "Redis Hash 设置和获取失败"
    assert field2_value == "value2", "Redis Hash 设置和获取失败"
    
    # 获取所有字段
    all_fields = redis_client.hgetall(test_hash)
    assert len(all_fields) == 2, "Redis Hash 获取所有字段失败"
    
    # 测试删除
    redis_client.delete(test_hash)
    assert redis_client.hgetall(test_hash) == {}, "Redis Hash 删除失败"
