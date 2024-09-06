from django.apps import AppConfig
from reconPoint.definitions import logger


class StartscanConfig(AppConfig):
    name = 'startScan'

    def ready(self):
        '''
        Any Scans that were incomplete in the last scan, we will mark them failed after
        server restarted
        This does not include pending_scans, pending_scans are taken care by celery
        '''
        pass
