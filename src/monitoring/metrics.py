from prometheus_client import Counter, Gauge, Histogram


xlsx_parse_total = Counter(
    "xlsx_parse_total",
    "Total number of XLSX parsing attempts",
)

xlsx_parse_failures_total = Counter(
    "xlsx_parse_failures_total",
    "Total number of XLSX parsing failures",
)

xlsx_parse_duration_seconds = Histogram(
    "xlsx_parse_duration_seconds",
    "Time spent parsing XLSX files",
)

query_total = Counter(
    "query_total",
    "Total number of user queries",
)

query_failures_total = Counter(
    "query_failures_total",
    "Total number of failed queries",
)

query_duration_seconds = Histogram(
    "query_duration_seconds",
    "Time spent processing queries",
)

validation_failures_total = Counter(
    "validation_failures_total",
    "Total number of validation failures",
)

app_health = Gauge(
    "app_health",
    "Application health status",
)