from rest_framework.throttling import UserRateThrottle


class ScanRateThrottle(UserRateThrottle):
    rate = "10/minute"
    scope = "scan"


class ExportRateThrottle(UserRateThrottle):
    rate = "5/minute"
    scope = "export"


class SearchRateThrottle(UserRateThrottle):
    rate = "30/minute"
    scope = "search"


class DataImportRateThrottle(UserRateThrottle):
    rate = "20/minute"
    scope = "import"
