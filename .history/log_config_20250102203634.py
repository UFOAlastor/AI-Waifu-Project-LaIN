# config.py

import logging
import logging.handlers

# 日志配置
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "%(levelname)s [%(asctime)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",  # 日志文件位置
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,  # 最多保留5个日志备份
            "formatter": "default",
        },
    },
    "loggers": {
        "": {  # 根记录器
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "module1": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "module2": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def setup_logging():
    logging.config.dictConfig(LOG_CONFIG)
    logging.info("Logging setup complete.")


# 初始化日志
setup_logging()
