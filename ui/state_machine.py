"""UI 状态机核心实现。

管理 UI 状态流转、事件分发和上下文数据。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from ui.events import Event, EventType

logger = logging.getLogger(__name__)


class State(Enum):
    """UI 状态枚举。"""
    
    IDLE = "idle"                    # 空闲，可操作
    CONFIGURING = "configuring"      # Provider/参数变更中


# 定义合法的状态转换
VALID_TRANSITIONS: Dict[State, Set[State]] = {
    State.IDLE: {State.CONFIGURING},
    State.CONFIGURING: {State.IDLE},
}


@dataclass
class StateContext:
    """状态机上下文数据。
    
    存储跨状态共享的数据。
    """
    
    # Provider 相关
    current_provider: str = ""
    current_model: str = ""
    provider_tokens: Dict[str, str] = field(default_factory=dict)
    provider_prompt_hints: Dict[str, str] = field(default_factory=dict)
    
    # 生成结果
    last_error: Optional[str] = None
    last_elapsed_seconds: float = 0.0
    slider_temp_paths: List[str] = field(default_factory=list)
    
    def get_token(self, provider: str) -> str:
        """获取指定 provider 的 token。"""
        return self.provider_tokens.get(provider, "")
    
    def set_token(self, provider: str, token: str) -> None:
        """设置指定 provider 的 token。"""
        self.provider_tokens[provider] = token
    
    def get_prompt_hint(self, provider: str) -> str:
        """获取指定 provider 的 prompt 提示。"""
        return self.provider_prompt_hints.get(provider, "")
    
    def set_prompt_hint(self, provider: str, hint: str) -> None:
        """设置指定 provider 的 prompt 提示。"""
        self.provider_prompt_hints[provider] = hint

    def replace_slider_temp_paths(self, temp_paths: List[str]) -> None:
        """Replace managed slider temp files and delete stale files."""
        next_paths = list(temp_paths)
        stale_paths = set(self.slider_temp_paths) - set(next_paths)

        for stale_path in stale_paths:
            try:
                Path(stale_path).unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to remove stale slider temp file: %s", stale_path)

        self.slider_temp_paths = next_paths


class StateMachine:
    """UI 状态机。
    
    职责：
    - 管理当前状态
    - 处理状态转换逻辑
    - 分发事件给订阅者
    - 验证转换合法性
    
    使用观察者模式，组件可订阅状态变更通知。
    """
    
    def __init__(self, initial_state: State = State.IDLE):
        """初始化状态机。
        
        Args:
            initial_state: 初始状态，默认为 IDLE
        """
        self._state = initial_state
        self._context = StateContext()
        self._subscribers: List[Callable[[State, StateContext], None]] = []
    
    @property
    def state(self) -> State:
        """当前状态（只读）。"""
        return self._state
    
    @property
    def context(self) -> StateContext:
        """上下文数据（只读引用）。"""
        return self._context
    
    def subscribe(self, callback: Callable[[State, StateContext], None]) -> None:
        """订阅状态变更通知。
        
        Args:
            callback: 回调函数，接收 (new_state, context) 参数
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[State, StateContext], None]) -> None:
        """取消订阅。
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def transition(self, event: Event) -> bool:
        """触发状态转换。
        
        根据事件类型决定目标状态，验证转换合法性后执行转换。
        
        Args:
            event: 触发事件
            
        Returns:
            转换是否成功
        """
        target_state = self._get_target_state(event)
        
        if target_state is None:
            logger.warning(
                "Event %s does not trigger state transition in %s",
                event.type.value,
                self._state.value,
            )
            return False
        
        if target_state not in VALID_TRANSITIONS.get(self._state, set()):
            logger.warning(
                "Invalid transition: %s -> %s (event: %s)",
                self._state.value,
                target_state.value,
                event.type.value,
            )
            return False
        
        # 执行转换
        old_state = self._state
        self._state = target_state
        
        # 更新上下文
        self._update_context(event)
        
        logger.info(
            "State transition: %s -> %s (event: %s)",
            old_state.value,
            target_state.value,
            event.type.value,
        )
        
        # 通知订阅者
        self._notify_subscribers()
        
        return True
    
    def _get_target_state(self, event: Event) -> Optional[State]:
        """根据事件类型确定目标状态。
        
        Args:
            event: 触发事件
            
        Returns:
            目标状态，如果事件不触发状态转换则返回 None
        """
        event_state_map = {
            EventType.PROVIDER_CHANGED: State.CONFIGURING,
            EventType.CONFIG_UPDATED: State.IDLE,
        }
        return event_state_map.get(event.type)
    
    def _update_context(self, event: Event) -> None:
        """根据事件更新上下文数据。
        
        Args:
            event: 触发事件
        """
        payload = event.payload or {}
        
        if event.type == EventType.PROVIDER_CHANGED:
            if "provider" in payload:
                self._context.current_provider = payload["provider"]
    
    def _notify_subscribers(self) -> None:
        """通知所有订阅者状态变更。"""
        for callback in self._subscribers:
            try:
                callback(self._state, self._context)
            except Exception as e:
                logger.exception(
                    "Error in state change subscriber %s: %s",
                    callback.__name__,
                    e,
                )
