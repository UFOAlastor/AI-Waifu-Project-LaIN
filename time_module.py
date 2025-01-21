# time_module.py

from datetime import datetime


class DateTime:
    def __init__(self):
        self.weekday_map = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日",
        }

    def get_current_datetime(self):
        """获取当前日期与时间"""
        return datetime.now()

    def format_datetime(self, dt):
        """格式化日期与时间为语言描述"""
        # 转为初步格式化字符串
        formatted_date_time = dt.strftime("%Y年%m月%d日 %A %H点%M分%S秒")
        # 替换英文星期为中文星期
        for eng, cn in self.weekday_map.items():
            formatted_date_time = formatted_date_time.replace(eng, cn)
        return formatted_date_time

    def get_formatted_current_datetime(self):
        """直接获取格式化后的当前日期与时间"""
        current_dt = self.get_current_datetime()
        return self.format_datetime(current_dt)


# 使用示例
if __name__ == "__main__":
    dt_formatter = DateTime()
    formatted_time = dt_formatter.get_formatted_current_datetime()
    print("当前日期和时间是：", formatted_time)
