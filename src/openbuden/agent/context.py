"""Shared context manager for Hive agents."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set


class SharedContext:
    def __init__(self) -> None:
        self.messages: List[Dict[str, str]] = []
        self._seen_message_ids: Set[str] = set()

    def add_message(
        self,
        role: str,
        content: str,
        name: str,
        message_id: Optional[str] = None,
    ) -> None:
        if message_id is not None:
            if message_id in self._seen_message_ids:
                return
            self._seen_message_ids.add(message_id)
        self.messages.append(
            {
                "role": role,
                "content": content,
                "name": name,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_history(self) -> List[Dict[str, str]]:
        return list(self.messages)

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        return [
            {
                "role": message["role"],
                "content": f"[{message['name']}]: {message['content']}",
            }
            for message in self.messages
        ]

    def get_last_n(self, n: int) -> List[Dict[str, str]]:
        return list(self.messages[-n:])
