from django.core.management.base import BaseCommand
from reconPoint.common_func import dump_custom_scan_engines


class Command(BaseCommand):
    help = 'Dumps custom engines into YAMLs in custom_engines/ folder'

    @staticmethod
    def handle(*args, **kwargs):
        return dump_custom_scan_engines('/usr/src/app/custom_engines')