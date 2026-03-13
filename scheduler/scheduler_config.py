from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

import logging

logger = logging.getLogger(__name__)

# Хранилище джобов в SQLAlchemy
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///tasks.db')  
}

# Executor для asyncio
executors = {
    'default': AsyncIOExecutor()
}

# Конфигурация планировщика
scheduler_config = {
    'jobstores': jobstores,
    'executors': executors,
    'job_defaults': {
        'coalesce': False,  # Не объединять пропущенные выполнения
        'max_instances': 1,  # Максимум 1 экземпляр джобы одновременно
        'misfire_grace_time': None  # Выполнять даже с опозданием
    }
}

# Глобальный объект scheduler
scheduler = AsyncIOScheduler(**scheduler_config)


def init_scheduler():
    """Инициализация и запуск планировщика"""
    scheduler.start()
    logger.info("APScheduler запущен")


def shutdown_scheduler():
    """Остановка планировщика"""
    scheduler.shutdown(wait=False)
    logger.info("APScheduler остановлен")