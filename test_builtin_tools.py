#!/usr/bin/env python3
"""测试内置工具系统"""
import asyncio
from app.core.tool_bootstrap import init_builtin_tools
from app.domain.tool.executor import DefaultToolExecutor

async def test_tool_system():
    """测试工具系统的基本功能"""
    print("=== 初始化内置工具系统 ===")
    registry = init_builtin_tools()
    
    print(f"\n=== 工具统计 ===")
    print(f"工具总数: {registry.get_tool_count()}")
    print(f"提供者数量: {registry.get_provider_count()}")
    
    print("\n=== 工具列表 ===")
    tools = registry.list_tools()
    for tool in tools:
        print(f"- {tool.name}: {tool.description} (type: {tool.tool_type.value})")
    
    print("\n=== 测试工具执行 ===")
    executor = DefaultToolExecutor(registry)
    
    # 测试系统信息工具
    print("\n1. 测试 system_info 工具:")
    system_info_result = await executor.execute("system_info", {"details": True})
    print(f"成功: {system_info_result.success}")
    if system_info_result.success:
        print(f"系统: {system_info_result.data.os}")
        print(f"版本: {system_info_result.data.version}")
        print(f"CPU: {system_info_result.data.cpu} 核心")
        print(f"内存: {system_info_result.data.memory} MB")
    
    # 测试文件列表工具
    print("\n2. 测试 file_list 工具:")
    file_list_result = await executor.execute("file_list", {"directory": ".", "pattern": "*.py"})
    print(f"成功: {file_list_result.success}")
    if file_list_result.success:
        print(f"找到 {len(file_list_result.data.files)} 个 Python 文件")
        for file in file_list_result.data.files[:5]:  # 只显示前5个
            print(f"  - {file}")
    
    # 测试 RAG 搜索工具
    print("\n3. 测试 rag_search 工具:")
    rag_result = await executor.execute("rag_search", {
        "query": "测试查询",
        "dataset_id": "test_dataset",
        "top_k": 2
    })
    print(f"成功: {rag_result.success}")
    if rag_result.success:
        print(f"返回 {len(rag_result.data)} 个结果")
        for i, item in enumerate(rag_result.data):
            print(f"  {i+1}. 分数: {item.score}, 内容: {item.content[:50]}...")
    
    # 测试数据解析工具
    print("\n4. 测试 data_parse 工具:")
    json_data = '{"name": "test", "value": 123}'
    data_parse_result = await executor.execute("data_parse", {
        "data": json_data,
        "format": "json"
    })
    print(f"成功: {data_parse_result.success}")
    if data_parse_result.success:
        print(f"解析结果: {data_parse_result.data.parsed}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_tool_system())
