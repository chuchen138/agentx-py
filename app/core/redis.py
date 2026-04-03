import os
from dotenv import load_dotenv

load_dotenv()

# 尝试导入aioredis，如果失败则使用mock
try:
    import aioredis
    
    # Redis配置
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # 创建Redis客户端
    redis_client = aioredis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        password=REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True
    )
    
    async def close_redis():
        """关闭Redis连接"""
        await redis_client.close()
except ImportError:
    # 当aioredis不可用时，使用mock实现
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None, nx=None):
            self.data[key] = value
            return True
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True
        
        async def brpop(self, key, timeout=None):
            return None
        
        async def lpush(self, key, value):
            if key not in self.data:
                self.data[key] = []
            self.data[key].insert(0, value)
            return len(self.data[key])
        
        async def close(self):
            pass
    
    redis_client = MockRedis()
    
    async def close_redis():
        """关闭Redis连接"""
        pass
