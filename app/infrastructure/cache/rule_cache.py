from collections import OrderedDict
from typing import Optional, Dict, Any
import json
import redis
from app.domain.rule.model import RuleEntity


class LRUCache:
    """本地 LRU 缓存"""
    def __init__(self, maxsize=100):
        self.cache = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, key: str) -> Optional[RuleEntity]:
        """获取缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: RuleEntity):
        """设置缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def pop(self, key: str):
        """删除缓存"""
        self.cache.pop(key, None)


class RuleCache:
    """规则多级缓存"""
    
    def __init__(self):
        self.local_cache = LRUCache(maxsize=100)
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    async def get(self, handler_key: str) -> Optional[RuleEntity]:
        """获取规则缓存"""
        # 1. 尝试本地缓存
        if rule := self.local_cache.get(handler_key):
            return rule
        
        # 2. 尝试 Redis 缓存
        try:
            cached = self.redis_client.get(f"rule:{handler_key}")
            if cached:
                rule_data = json.loads(cached)
                # 重建 RuleEntity 对象
                rule = RuleEntity(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    handler_key=rule_data['handler_key'],
                    description=rule_data['description'],
                    config=rule_data['config'],
                    enabled=rule_data['enabled'],
                    priority=rule_data['priority'],
                    version=rule_data['version']
                )
                self.local_cache.set(handler_key, rule)
                return rule
        except Exception:
            # Redis 连接失败时忽略
            pass
        
        return None
    
    async def set(self, handler_key: str, rule: RuleEntity):
        """设置规则缓存"""
        # 1. 更新本地缓存
        self.local_cache.set(handler_key, rule)
        
        # 2. 更新 Redis 缓存
        try:
            rule_data = rule.dict()
            self.redis_client.setex(
                f"rule:{handler_key}",
                300,  # 5 分钟
                json.dumps(rule_data)
            )
        except Exception:
            # Redis 连接失败时忽略
            pass
    
    async def invalidate(self, handler_key: str):
        """缓存失效"""
        # 1. 删除本地缓存
        self.local_cache.pop(handler_key)
        
        # 2. 删除 Redis 缓存
        try:
            self.redis_client.delete(f"rule:{handler_key}")
            # 发布失效通知
            self.redis_client.publish("rule:invalidated", handler_key)
        except Exception:
            # Redis 连接失败时忽略
            pass


# 全局缓存实例
rule_cache = RuleCache()
