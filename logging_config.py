import os
import logging
import logging.config
import sys


def setup_logging():
    # 确保 logs 目录存在
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # 设置日志配置
    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
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
                # 使用 utf-8 编码
                "stream": sys.stdout,
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "default",
                # 使文件处理程序使用 UTF-8 编码
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "ui_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "vits_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "model_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "replyParser_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "asr_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "micButton_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "vpr_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # 日志初始化
    logging.config.dictConfig(LOG_CONFIG)
    logging.info("Logging setup complete.")


if __name__ == "__main__":
    setup_logging()
