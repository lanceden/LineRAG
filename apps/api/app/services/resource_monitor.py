"""
資源監控和清理任務
"""

import asyncio
import logging
from typing import Dict, Any
from app.services.multitenant_rag import get_multitenant_rag_service

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """資源監控器"""

    def __init__(self):
        self.rag_service = get_multitenant_rag_service()
        self.monitoring_interval = 300  # 5分鐘
        self.cleanup_interval = 3600  # 1小時
        self.is_running = False

    async def start_monitoring(self):
        """啟動資源監控"""
        if self.is_running:
            logger.warning("資源監控已在運行中")
            return

        self.is_running = True
        logger.info("🚀 啟動資源監控任務")

        # 啟動監控任務
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._cleanup_loop())

    async def stop_monitoring(self):
        """停止資源監控"""
        self.is_running = False
        logger.info("🛑 停止資源監控任務")

    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                await self._perform_monitoring()
            except Exception as e:
                logger.error(f"資源監控循環出錯: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def _cleanup_loop(self):
        """清理循環"""
        while self.is_running:
            try:
                await self._perform_cleanup()
            except Exception as e:
                logger.error(f"資源清理循環出錯: {e}")

            await asyncio.sleep(self.cleanup_interval)

    async def _perform_monitoring(self):
        """執行資源監控"""
        try:
            # 獲取整體資源統計
            stats = await self.rag_service.get_resource_monitoring_stats()

            # 記錄關鍵指標
            total_companies = stats.get("total_companies", 0)
            active_pools = stats.get("active_processing_pools", 0)

            logger.info(
                f"📊 資源監控 - 公司數: {total_companies}, 活躍線程池: {active_pools}"
            )

            # 檢查各公司的資源使用情況
            company_resources = stats.get("company_resources", {})
            for company_id, resources in company_resources.items():
                if isinstance(resources, dict) and "overall_status" in resources:
                    status = resources["overall_status"]
                    if status in ["warning", "critical"]:
                        logger.warning(f"⚠️ 公司 {company_id} 資源狀態: {status}")

                        # 記憶體使用率
                        memory = resources.get("memory", {})
                        if memory.get("usage_percent", 0) > 80:
                            logger.warning(
                                f"   記憶體使用率: {memory['usage_percent']:.1f}%"
                            )

                        # 儲存使用率
                        storage = resources.get("storage", {})
                        if storage.get("usage_percent", 0) > 80:
                            logger.warning(
                                f"   儲存使用率: {storage['usage_percent']:.1f}%"
                            )

        except Exception as e:
            logger.error(f"執行資源監控失敗: {e}")

    async def _perform_cleanup(self):
        """執行資源清理"""
        try:
            logger.info("🧹 開始定期資源清理")

            # 清理過期的公司服務
            cleanup_result = await self.rag_service.cleanup_inactive_services()
            if cleanup_result.get("cleaned_up", 0) > 0:
                logger.info(f"清理了 {cleanup_result['cleaned_up']} 個非活躍服務")

            # 清理各公司的舊資料（30天前）
            company_resources = (
                await self.rag_service.get_resource_monitoring_stats()
            ).get("company_resources", {})

            for company_id in company_resources.keys():
                try:
                    cleanup_result = await self.rag_service.cleanup_company_resources(
                        int(company_id), days_old=30
                    )
                    if cleanup_result.get("cleaned_files", 0) > 0:
                        logger.info(
                            f"公司 {company_id}: {cleanup_result['cleaned_files']} 檔案已清理"
                        )
                except Exception as e:
                    logger.error(f"清理公司 {company_id} 資源失敗: {e}")

            logger.info("✅ 定期資源清理完成")

        except Exception as e:
            logger.error(f"執行資源清理失敗: {e}")

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """獲取監控報告"""
        try:
            resource_stats = await self.rag_service.get_resource_monitoring_stats()
            pool_stats = await self.rag_service.monitor_processing_pool_health()

            return {
                "resource_stats": resource_stats,
                "pool_stats": pool_stats,
                "monitoring_status": "active" if self.is_running else "inactive",
                "intervals": {
                    "monitoring": self.monitoring_interval,
                    "cleanup": self.cleanup_interval,
                },
            }

        except Exception as e:
            logger.error(f"獲取監控報告失敗: {e}")
            return {"error": str(e)}


# 全域監控器實例
_resource_monitor = None


def get_resource_monitor() -> ResourceMonitor:
    """取得資源監控器單例"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


async def start_resource_monitoring():
    """啟動資源監控（應用啟動時調用）"""
    monitor = get_resource_monitor()
    await monitor.start_monitoring()
    return monitor


async def stop_resource_monitoring():
    """停止資源監控（應用關閉時調用）"""
    monitor = get_resource_monitor()
    await monitor.stop_monitoring()
