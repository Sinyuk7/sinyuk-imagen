"""UI 状态机事件定义。

定义状态机支持的所有事件类型和事件数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    """状态机事件类型枚举。"""
    
    # Provider 相关
    PROVIDER_CHANGED = "provider_changed"

    # 配置更新完成
    CONFIG_UPDATED = "config_updated"


@dataclass
class Event:
    """事件数据结构。
    
    Attributes:
        type: 事件类型
        payload: 事件携带的数据
        source: 事件来源标识（用于调试）
    """
    
    type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    
    def __post_init__(self) -> None:
        """确保 payload 是字典。"""
        if self.payload is None:
            self.payload = {}
