from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class StarkappConfig(AppConfig):
    name = 'starkapp'

    # 程序启动时，扫描app下得指定文件（stark1.py）并执行
    def ready(self):
        autodiscover_modules('stark1')
