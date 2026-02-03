"""Tool execution entry point for Hive agents."""

from __future__ import annotations

from typing import Dict, Optional

from hive.config.schema import ToolConfig
from hive.tools.mcp_bridge import MCPBridge
from hive.tools.registry import ToolRegistry
from hive.tools.scheduler import ScheduleStore


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        mcp_bridge: MCPBridge,
        schedule_store: Optional[ScheduleStore] = None,
    ) -> None:
        self.registry = registry
        self.mcp_bridge = mcp_bridge
        self.schedule_store = schedule_store

    async def run(
        self,
        agent_name: str,
        agent_tools: list[ToolConfig],
        tool_name: str,
        action: str,
        params: Dict,
    ) -> Optional[Dict]:
        allowed = (
            True
            if tool_name == "schedule"
            else self.registry.has_permission(agent_name, tool_name, action, agent_tools)
        )
        if not allowed:
            print(
                f"Permission denied: {agent_name} cannot {action} on {tool_name}"
            )
            return None
        if tool_name == "schedule" and self.schedule_store is not None:
            return self._handle_schedule(agent_name, params)
        return await self.mcp_bridge.execute(tool_name, action, params)

    def _handle_schedule(self, agent_name: str, params: Dict) -> Optional[Dict]:
        if self.schedule_store is None:
            return None
        task = str(params.get("task")) if params.get("task") else ""
        schedule_type = str(params.get("type")) if params.get("type") else ""
        interval = params.get("interval_minutes")
        cron = str(params.get("cron")) if params.get("cron") else None
        channel_id = params.get("channel_id")
        action = str(params.get("action") or "").lower()
        if action == "list":
            jobs = self.schedule_store.list_jobs(agent_name=agent_name)
            return {"status": "ok", "jobs": [job.__dict__ for job in jobs]}
        if action == "delete":
            job_id = str(params.get("job_id") or "")
            if not job_id:
                return None
            removed = self.schedule_store.remove_job(job_id, agent_name=agent_name)
            return {"status": "ok" if removed else "not_found", "job_id": job_id}

        if not task or schedule_type not in {"interval", "cron"}:
            return None
        job = self.schedule_store.add_job(
            agent_name=agent_name,
            task=task,
            schedule_type=schedule_type,
            interval_minutes=_safe_int(interval),
            cron=cron,
            channel_id=_safe_int(channel_id),
        )
        return {
            "status": "scheduled",
            "job_id": job.job_id,
            "next_run": job.next_run,
        }


def _safe_int(value: object) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
