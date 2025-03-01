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
            "lettaModel_module": {
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
            "live2d_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "lipsync_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "mem0_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "history_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "openaiTypeModel_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "ollamaModel_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # 日志初始化
    logging.config.dictConfig(LOG_CONFIG)
    logging.info("Logging setup complete.")


def gcww(config_dict, key, default_value, logger):
    """获取配置文件信息, 缺失则弹出警告 (Get Config With Warning)

    Args:
        config_dict (dict): 配置文件dict
        key (str): 配置项名称
        default_value (_type_): 配置项默认值
        logger (logging): logging工具

    Returns:
        _type_: 返回配置值 (加载失败则warning并返回默认值)
    """
    if key not in config_dict:
        logger.warning(f"配置项'{key}'没有加载成功, 使用默认值: {default_value}")
        return default_value
    return config_dict[key]


if __name__ == "__main__":
    setup_logging()
