from prometheus_client import Counter, Histogram, Gauge

# 文件上传成功率指标
file_upload_success = Counter(
    'file_upload_success_total',
    'Total number of successful file uploads',
    ['file_type', 'storage_backend']
)

file_upload_failure = Counter(
    'file_upload_failure_total',
    'Total number of failed file uploads',
    ['file_type', 'error_type']
)

# 上传耗时直方图
file_upload_duration = Histogram(
    'file_upload_duration_seconds',
    'Duration of file upload operations',
    ['file_type']
)

# 存储使用量统计
file_storage_used = Gauge(
    'file_storage_used_bytes',
    'Total storage used by files',
    ['file_type']
)

# 各类型文件数量统计
file_count = Gauge(
    'file_count_total',
    'Total number of files stored',
    ['file_type']
)

# 缓存命中率指标
file_cache_hit = Counter(
    'file_cache_hit_total',
    'Total number of file cache hits'
)

file_cache_miss = Counter(
    'file_cache_miss_total',
    'Total number of file cache misses'
)

# 错误类型分布
file_error_count = Counter(
    'file_error_count_total',
    'Total number of file operation errors',
    ['error_type']
)
