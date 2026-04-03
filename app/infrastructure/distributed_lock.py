import uuid
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class DistributedLock:
    """分布式锁实现（基于 Redis SETNX）"""

    def __init__(self, lock_key: str, timeout: int = 300, redis_client=None):
        """
        初始化分布式锁

        Args:
            lock_key: 锁的键名
            timeout: 锁超时时间（秒），默认5分钟
            redis_client: Redis 客户端实例
        """
        self.lock_key = f"distributed_lock:{lock_key}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.redis = redis_client
        self._locked = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def acquire(self, blocking: bool = True, blocking_timeout: int = 10) -> bool:
        """
        获取锁

        Args:
            blocking: 是否阻塞等待
            blocking_timeout: 阻塞等待超时时间（秒）

        Returns:
            是否成功获取锁
        """
        if not self.redis:
            self.logger.warning("Redis not available, lock acquisition skipped")
            return True

        start_time = time.time()

        while True:
            try:
                # 使用 SET NX EX 原子操作
                acquired = self.redis.set(
                    self.lock_key,
                    self.token,
                    nx=True,  # 仅当不存在时设置
                    ex=self.timeout
                )

                if acquired:
                    self._locked = True
                    self.logger.debug(f"Lock acquired: {self.lock_key}")
                    return True

                if not blocking:
                    return False

                # 检查是否超时
                if time.time() - start_time >= blocking_timeout:
                    self.logger.debug(f"Lock acquisition timeout: {self.lock_key}")
                    return False

                # 短暂休眠后重试
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error acquiring lock: {e}")
                if not blocking:
                    return False
                time.sleep(0.5)

    def release(self) -> bool:
        """
        释放锁

        Returns:
            是否成功释放
        """
        if not self.redis:
            return True

        if not self._locked:
            return False

        try:
            # 使用 Lua 脚本保证原子性
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = self.redis.eval(lua_script, 1, self.lock_key, self.token)

            if result:
                self._locked = False
                self.logger.debug(f"Lock released: {self.lock_key}")
                return True
            else:
                self.logger.warning(f"Lock release failed (not owner): {self.lock_key}")
                return False

        except Exception as e:
            self.logger.error(f"Error releasing lock: {e}")
            return False

    def extend(self, additional_time: int) -> bool:
        """
        延长锁的超时时间

        Args:
            additional_time: 额外时间（秒）

        Returns:
            是否成功延长
        """
        if not self.redis:
            return True

        if not self._locked:
            return False

        try:
            # 使用 Lua 脚本保证原子性
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = self.redis.eval(
                lua_script, 1, self.lock_key, self.token,
                str(self.timeout + additional_time)
            )
            return bool(result)

        except Exception as e:
            self.logger.error(f"Error extending lock: {e}")
            return False

    def is_locked(self) -> bool:
        """检查当前实例是否持有锁"""
        return self._locked

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class ScheduledTaskLock(DistributedLock):
    """定时任务专用分布式锁"""

    def __init__(self, task_id: str, execute_time: datetime, redis_client=None):
        """
        初始化定时任务锁

        Args:
            task_id: 任务ID
            execute_time: 执行时间，用于生成唯一锁key
            redis_client: Redis 客户端实例
        """
        lock_key = f"scheduled_task:lock:{task_id}:{int(execute_time.timestamp())}"
        # 锁超时时间：30分钟 + 5分钟缓冲
        super().__init__(lock_key, timeout=2100, redis_client=redis_client)
        self.task_id = task_id
        self.execute_time = execute_time


class IdempotencyManager:
    """幂等性管理器"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_and_set(self, task_id: str, execute_time: datetime, expire_seconds: int = 7200) -> bool:
        """
        检查并设置幂等键

        Args:
            task_id: 任务ID
            execute_time: 执行时间
            expire_seconds: 过期时间（秒），默认2小时

        Returns:
            True 表示可以执行（新键），False 表示已存在（重复执行）
        """
        if not self.redis:
            return True

        key = f"idem:{task_id}:{int(execute_time.timestamp())}"

        try:
            # SET NX 命令：仅当键不存在时设置
            result = self.redis.set(key, "1", nx=True, ex=expire_seconds)
            return bool(result)
        except Exception as e:
            self.logger.error(f"Error checking idempotency: {e}")
            # 出错时允许执行，由业务层保证幂等
            return True

    def clear(self, task_id: str, execute_time: datetime):
        """清除幂等键"""
        if not self.redis:
            return

        key = f"idem:{task_id}:{int(execute_time.timestamp())}"

        try:
            self.redis.delete(key)
        except Exception as e:
            self.logger.error(f"Error clearing idempotency key: {e}")
