"""
Async logging utilities để tối ưu hiệu năng
Ghi log vào Elasticsearch mà không block response
"""
from fastapi import BackgroundTasks
import time
from typing import Any, Dict

async def log_to_elasticsearch(es_client, event_data: Dict[str, Any]):
    """
    Background task để ghi log vào Elasticsearch
    Không raise exception để tránh ảnh hưởng tới request chính
    """
    try:
        await es_client.post("/analytics/_doc", json=event_data)
    except Exception as e:
        # Log error nhưng không fail - có thể thêm fallback logging
        print(f"[ES_LOG_ERROR] Failed to log event: {e}")


def create_log_event(
    event_type: str,
    user_id: str = None,
    latency_ms: int = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper function để tạo event data structure
    """
    event = {
        "timestamp": int(time.time() * 1000),
        "event_type": event_type,
    }
    
    if user_id:
        event["user_id"] = user_id
    
    if latency_ms is not None:
        event["latency_ms"] = latency_ms
    
    # Thêm các fields khác
    event.update(kwargs)
    
    return event


class ESLogger:
    """
    Wrapper class để quản lý logging với background tasks
    """
    def __init__(self, es_client, background_tasks: BackgroundTasks = None):
        self.es_client = es_client
        self.background_tasks = background_tasks
    
    def log_event(self, event_type: str, **kwargs):
        """
        Log event - sử dụng background task nếu có
        """
        event_data = create_log_event(event_type, **kwargs)
        
        if self.background_tasks:
            # Async logging - không block response
            self.background_tasks.add_task(
                log_to_elasticsearch,
                self.es_client,
                event_data
            )
        else:
            # Fallback - fire and forget
            import asyncio
            try:
                asyncio.create_task(log_to_elasticsearch(self.es_client, event_data))
            except:
                pass
    
    async def log_event_sync(self, event_type: str, **kwargs):
        """
        Log event synchronously (chỉ dùng khi cần thiết)
        """
        event_data = create_log_event(event_type, **kwargs)
        await log_to_elasticsearch(self.es_client, event_data)