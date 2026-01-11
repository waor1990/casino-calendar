"""Unified logging setup for Casino Calendar."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from importlib import import_module, util
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Iterable

_LOGGING_LOCK = threading.RLock()

_HANDLER_ROLE_ATTR = "_casino_handler_role"
_CONSOLE_ROLE = "console"
_FILE_ROLE = "file"
_DEBUG_FILE_ROLE = "file_debug"

_HTTP_LOGGER_NAMES = (
    "werkzeug",
    "waitress",
    "gunicorn.access",
    "uvicorn.access",
    "cherrypy.access",
)

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_MINIMAL_LOG_PREFIXES = (
    "Production logging initialized",
    "Logging system initialized",
    "Logging system shutting down",
)

_MAINTENANCE_EMBEDDED_LOG_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z \| (DBG|INF|WRN|ERR|CRT)\s+\|")

_REDACTION_PATTERN = re.compile(
    r"(?i)\b(api_key|apikey|password|passwd|secret|token|authorization|bearer)\b\s*([:=])\s*([^\s,|]+)"
)
_HEADER_REDACTION_PATTERN = re.compile(r"(?i)\b(authorization|cookie|set-cookie)\b\s*[:=]\s*([^\n]+)")
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+([^\s,|]+)")

_HTTP_LOG_BASE_PATH: Path | None = None
_HTTP_FILE_HANDLER: TimedRotatingFileHandler | None = None
_HTTP_SUPPRESSION_FILTER: "_HttpSuppressionFilter | None" = None


def _find_spec(module_name: str) -> bool:
    return util.find_spec(module_name) is not None


def _get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _coerce_log_level(level_name: str, fallback: int = logging.INFO) -> int:
    return _LEVEL_MAP.get(level_name.upper(), fallback)


def get_log_level(env_var: str = "LOG_LEVEL", default: str = "INFO") -> int:
    configured = os.getenv(env_var)
    fallback = _coerce_log_level(default, logging.INFO)
    if configured:
        return _coerce_log_level(configured, fallback)
    return fallback


def _redact_text(value: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        separator = match.group(2)
        return f"{key}{separator}****"

    redacted = _REDACTION_PATTERN.sub(_replace, value)
    redacted = _HEADER_REDACTION_PATTERN.sub(lambda m: f"{m.group(1)}=****", redacted)
    redacted = _BEARER_PATTERN.sub("bearer ****", redacted)
    return redacted


class _RedactingFormatter(logging.Formatter):
    def _apply_redaction(self, message: str) -> str:
        return _redact_text(message)


def _level_code(levelno: int) -> str:
    if levelno >= logging.CRITICAL:
        return "CRT"
    if levelno >= logging.ERROR:
        return "ERR"
    if levelno >= logging.WARNING:
        return "WRN"
    if levelno >= logging.INFO:
        return "INF"
    return "DBG"


def _format_callsite(record: logging.LogRecord) -> str:
    return f"{record.module}:{record.funcName}:{record.lineno}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _utc_iso_ms(epoch_seconds: float | None = None) -> str:
    timestamp = _now_utc() if epoch_seconds is None else datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("UTC timestamp must be timezone-aware")
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _console_timestamp(record: logging.LogRecord) -> str:
    mode = os.getenv("LOG_CONSOLE_TZ", "LOCAL").upper()
    if mode == "UTC":
        return datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%SZ")
    return datetime.fromtimestamp(record.created, tz=_now_local().tzinfo).strftime("%H:%M:%S")


def _console_debug_context_enabled() -> bool:
    return os.getenv("LOG_LEVEL", "").upper() == "DEBUG"


class ConsoleFormatter(_RedactingFormatter):
    _ANSI_COLORS = {
        "DEBUG": "\x1b[36m",
        "INFO": "\x1b[32m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[35m",
    }
    _RICH_COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "magenta",
    }

    def __init__(self, *, use_colors: bool, use_rich_markup: bool) -> None:
        super().__init__()
        self._use_colors = use_colors
        self._use_rich_markup = use_rich_markup

    def format(self, record: logging.LogRecord) -> str:
        timestamp = _console_timestamp(record)
        level = _level_code(record.levelno)
        if self._use_colors:
            if self._use_rich_markup:
                color = self._RICH_COLORS.get(record.levelname)
                if color:
                    level = f"[{color}]{level}[/{color}]"
            else:
                color = self._ANSI_COLORS.get(record.levelname)
                if color:
                    level = f"{color}{level}\x1b[0m"

        minimal_console = _is_minimal_log_mode()
        location = _format_callsite(record)
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        if minimal_console:
            line = f"{timestamp} | {level} | {message}"
        else:
            line = f"{timestamp} | {level} | {location} | {message}"
            if _console_debug_context_enabled():
                request_id = getattr(record, "request_id", "-")
                user_id = getattr(record, "user_id", "-")
                if request_id not in {"", "-"} or user_id not in {"", "-"}:
                    line = f"{line} | req={request_id} user={user_id}"
        return self._apply_redaction(line)


class FileFormatter(_RedactingFormatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = _utc_iso_ms(record.created)
        level = _level_code(record.levelno)
        location = _format_callsite(record)
        service = getattr(record, "service", "-")
        environment = getattr(record, "env", "-")
        request_id = getattr(record, "request_id", "-")
        user_id = getattr(record, "user_id", "-")
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        line = (
            f"{timestamp} | {level} | {location} | pid={record.process} tid={record.thread} | "
            f"{message} | svc={service} env={environment} req={request_id} user={user_id}"
        )
        return self._apply_redaction(line)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = _utc_iso_ms(record.created).replace("Z", "")
        message = _redact_text(record.getMessage())
        payload = {
            "timestamp": timestamp,
            "tz": "UTC",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pid": record.process,
            "tid": record.thread,
            "service": getattr(record, "service", None),
            "env": getattr(record, "env", None),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "message": message,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class _ContextFilter(logging.Filter):
    def __init__(self, service: str, environment: str) -> None:
        super().__init__()
        self._service = service
        self._environment = environment

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        record.service = getattr(record, "service", self._service)
        record.env = getattr(record, "env", self._environment)
        record.request_id = getattr(record, "request_id", "-")
        record.user_id = getattr(record, "user_id", "-")
        return True


class _DedupingTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, *args, window_seconds: float = 2.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._window_seconds = window_seconds
        self._pending_record: logging.LogRecord | None = None
        self._pending_key: tuple[str, int, str] | None = None
        self._pending_time: float | None = None
        self._suppressed_count = 0

    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()
        try:
            self._emit_with_dedupe(record)
        finally:
            self.release()

    def _emit_with_dedupe(self, record: logging.LogRecord) -> None:
        key = (record.name, record.levelno, record.getMessage())
        now = time.time()
        if self._pending_record is None:
            self._store_pending(record, key, now)
            return

        if (
            self._pending_key == key
            and self._pending_time is not None
            and (now - self._pending_time) <= self._window_seconds
        ):
            self._suppressed_count += 1
            return

        self._emit_pending()
        self._store_pending(record, key, now)

    def flush(self) -> None:
        self.acquire()
        try:
            self._emit_pending()
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def close(self) -> None:
        try:
            self._emit_pending()
        finally:
            super().close()

    def _store_pending(self, record: logging.LogRecord, key: tuple[str, int, str], timestamp: float) -> None:
        self._pending_record = record
        self._pending_key = key
        self._pending_time = timestamp

    def _emit_pending(self) -> None:
        if self._pending_record is None:
            return
        record = self._pending_record
        if self._suppressed_count:
            suffix = f"(+{self._suppressed_count} duplicates suppressed)"
            record = _record_with_suffix(record, suffix)
        self._write_record(record)
        self._pending_record = None
        self._pending_key = None
        self._pending_time = None
        self._suppressed_count = 0

    def _write_record(self, record: logging.LogRecord) -> None:
        try:
            if self.shouldRollover(record):
                self.doRollover()
            message = self.format(record)
            stream = self.stream
            if stream is None:
                return
            stream.write(message + self.terminator)
            stream.flush()
        except Exception:
            self.handleError(record)


def _record_with_suffix(record: logging.LogRecord, suffix: str) -> logging.LogRecord:
    data = record.__dict__.copy()
    message = record.getMessage()
    data["msg"] = f"{message} {suffix}"
    data["args"] = ()
    return logging.makeLogRecord(data)


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.update(self.extra)
        return msg, kwargs


class _MinimalTestFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if not _is_minimal_log_mode():
            return True
        message = record.getMessage()
        return message.startswith(_MINIMAL_LOG_PREFIXES)


class _HttpSuppressionFilter(logging.Filter):
    def __init__(self, logger_names: Iterable[str]) -> None:
        super().__init__()
        self._logger_names = tuple(logger_names)
        self._notified = False

    def _matches(self, record: logging.LogRecord) -> bool:
        return any(record.name == name or record.name.startswith(f"{name}.") for name in self._logger_names)

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if self._matches(record) and record.levelno < logging.WARNING:
            if not self._notified:
                self._emit_notice(record)
                self._notified = True
            return False
        return True

    def _emit_notice(self, record: logging.LogRecord) -> None:
        message = (
            "HTTP request log suppressed from " f"{record.name} (set SUPPRESS_HTTP_LOGS=false to view HTTP traffic)"
        )
        try:
            print(message)
        except Exception:
            try:
                sys.stdout.write(message + "\n")
            except Exception:
                pass


class _MaintenanceDedupFilter(logging.Filter):
    def __init__(self, blocked_prefixes: Iterable[str]) -> None:
        super().__init__()
        self._blocked_prefixes = tuple(blocked_prefixes)

    def _is_blocked_logger(self, name: str) -> bool:
        return any(name == prefix or name.startswith(f"{prefix}.") for prefix in self._blocked_prefixes)

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if self._is_blocked_logger(record.name):
            return False
        message = record.getMessage()
        return _MAINTENANCE_EMBEDDED_LOG_RE.search(message) is None


def _is_minimal_log_mode() -> bool:
    value = os.getenv("CASINO_MINIMAL_TEST_LOG", "").lower()
    return value not in ("", "0", "false", "off", "no")


def _should_apply_minimal_filter(log_path: Path) -> bool:
    if not _is_minimal_log_mode():
        return False
    configured = os.getenv("LOG_FILE")
    candidates = {"app.log", "casino_calendar.log", "casino_calendar_prod.log"}
    if configured:
        candidates.add(Path(configured).name)
    return log_path.name in candidates


def _http_logs_are_suppressed() -> bool:
    return os.getenv("SUPPRESS_HTTP_LOGS", "True").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _derive_http_log_path(base_path: Path) -> Path:
    suffix = base_path.suffix or ".log"
    stem = base_path.stem
    if "casino_calendar" in stem:
        filename = f"casino_calendar_http{suffix}"
    else:
        filename = f"{stem}_http{suffix}"
    return base_path.with_name(filename)


def _get_http_suppression_filter() -> _HttpSuppressionFilter:
    global _HTTP_SUPPRESSION_FILTER
    if _HTTP_SUPPRESSION_FILTER is None:
        _HTTP_SUPPRESSION_FILTER = _HttpSuppressionFilter(_HTTP_LOGGER_NAMES)
    else:
        _HTTP_SUPPRESSION_FILTER._notified = False
    return _HTTP_SUPPRESSION_FILTER


def _get_maintenance_filter() -> _MaintenanceDedupFilter:
    return _MaintenanceDedupFilter(
        ("casino_calendar.tests", "casino_calendar.scripts.run_tests"),
    )


def _find_handler(logger: logging.Logger, role: str) -> logging.Handler | None:
    for handler in logger.handlers:
        if getattr(handler, _HANDLER_ROLE_ATTR, None) == role:
            return handler
    return None


def _apply_filter(handler: logging.Handler, filter_instance: logging.Filter | None) -> None:
    if filter_instance is None:
        handler.filters = [existing for existing in handler.filters if not isinstance(existing, _HttpSuppressionFilter)]
        return
    if filter_instance not in handler.filters:
        handler.addFilter(filter_instance)


def _resolve_log_dir(log_dir: str | None) -> Path:
    configured = log_dir or os.getenv("LOG_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path("logs")


def _resolve_log_path(log_file: str | None, log_dir: Path) -> Path:
    configured = log_file or os.getenv("LOG_FILE")
    if configured:
        return Path(configured).expanduser()
    return log_dir / "app.log"


def _resolve_debug_log_path(log_dir: Path, log_level: int) -> Path | None:
    configured = os.getenv("LOG_DEBUG_FILE")
    if configured is not None:
        if configured.strip() == "":
            return None
        return Path(configured).expanduser()
    if log_level <= logging.DEBUG:
        return log_dir / "app.debug.log"
    return None


def _build_console_handler(
    *,
    level: int,
    stream: object,
    http_filter: logging.Filter | None,
    service: str,
    environment: str,
) -> logging.Handler:
    is_tty = hasattr(stream, "isatty") and bool(stream.isatty())
    if _find_spec("rich.logging"):
        rich_logging = import_module("rich.logging")
        rich_console = import_module("rich.console")
        console = rich_console.Console(file=stream, force_terminal=is_tty)  # type: ignore[attr-defined]
        handler = rich_logging.RichHandler(  # type: ignore[attr-defined]
            console=console,
            show_time=False,
            show_level=False,
            show_path=False,
            markup=True,
            rich_tracebacks=False,
        )
        formatter = ConsoleFormatter(use_colors=is_tty, use_rich_markup=True)
    elif _find_spec("colorlog"):
        handler = logging.StreamHandler(stream)
        formatter = _build_colorlog_formatter()
    else:
        handler = logging.StreamHandler(stream)
        formatter = ConsoleFormatter(use_colors=is_tty, use_rich_markup=False)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(_ContextFilter(service, environment))
    _apply_filter(handler, http_filter)
    return handler


def _build_colorlog_formatter() -> logging.Formatter:
    colorlog = import_module("colorlog")

    class _ColorlogFormatter(colorlog.ColoredFormatter):  # type: ignore[attr-defined]
        def format(self, record: logging.LogRecord) -> str:
            return _redact_text(super().format(record))

    return _ColorlogFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s%(reset)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "purple",
        },
    )


def _ensure_context_filter(handler: logging.Handler, service: str, environment: str) -> None:
    for existing in handler.filters:
        if isinstance(existing, _ContextFilter):
            existing._service = service
            existing._environment = environment
            return
    handler.addFilter(_ContextFilter(service, environment))


def _build_file_formatter() -> logging.Formatter:
    if _get_env_bool("LOG_FILE_JSON", False):
        return JsonLogFormatter()
    return FileFormatter()


def _ensure_timed_file_handler(
    logger: logging.Logger,
    *,
    role: str,
    log_path: Path,
    level: int,
    retention_days: int,
    formatter: logging.Formatter,
    filters: Iterable[logging.Filter],
    dedupe: bool = True,
) -> TimedRotatingFileHandler:
    handler = _find_handler(logger, role)
    if handler is not None and isinstance(handler, TimedRotatingFileHandler):
        existing_path = Path(handler.baseFilename)
        if existing_path != log_path:
            logger.removeHandler(handler)
            try:
                handler.close()
            finally:
                handler = None
    else:
        handler = None

    if handler is None:
        handler_cls = _DedupingTimedRotatingFileHandler if dedupe else TimedRotatingFileHandler
        handler = handler_cls(
            str(log_path),
            when="midnight",
            interval=1,
            backupCount=retention_days,
            utc=True,
            encoding="utf-8",
        )
        setattr(handler, _HANDLER_ROLE_ATTR, role)
        logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    filter_list = list(filters)
    filter_types = {type(filter_instance) for filter_instance in filter_list}
    handler.filters = [existing for existing in handler.filters if type(existing) not in filter_types]
    for filter_instance in filter_list:
        handler.addFilter(filter_instance)
    return handler


def _teardown_http_log_handler() -> None:
    global _HTTP_FILE_HANDLER

    handler = _HTTP_FILE_HANDLER
    if handler is None:
        _configure_http_log_file_routing()
        return

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)
        if handler in http_logger.handlers:
            http_logger.removeHandler(handler)

    try:
        handler.close()
    finally:
        _HTTP_FILE_HANDLER = None
        _configure_http_log_file_routing()


def _ensure_http_file_handler(base_path: Path, formatter: logging.Formatter) -> None:
    global _HTTP_FILE_HANDLER, _HTTP_LOG_BASE_PATH

    _HTTP_LOG_BASE_PATH = base_path

    if _http_logs_are_suppressed():
        _teardown_http_log_handler()
        return

    http_log_path = _derive_http_log_path(base_path)
    http_log_path.parent.mkdir(parents=True, exist_ok=True)

    if _HTTP_FILE_HANDLER is not None:
        existing_path = Path(_HTTP_FILE_HANDLER.baseFilename)
        if existing_path == http_log_path:
            _ensure_context_filter(
                _HTTP_FILE_HANDLER,
                os.getenv("SERVICE_NAME", "casino_calendar"),
                os.getenv("APP_ENV", os.getenv("ENV", "local")),
            )
            _HTTP_FILE_HANDLER.setFormatter(formatter)
            _configure_http_log_file_routing()
            return
        _teardown_http_log_handler()

    handler = TimedRotatingFileHandler(
        str(http_log_path),
        when="midnight",
        interval=1,
        backupCount=14,
        utc=True,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    setattr(handler, "_casino_http_handler", True)
    _ensure_context_filter(
        handler,
        os.getenv("SERVICE_NAME", "casino_calendar"),
        os.getenv("APP_ENV", os.getenv("ENV", "local")),
    )

    _HTTP_FILE_HANDLER = handler
    _configure_http_log_file_routing()


def _configure_http_log_file_routing() -> None:
    handler = _HTTP_FILE_HANDLER

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)

        for existing in list(http_logger.handlers):
            if getattr(existing, "_casino_http_handler", False) and existing is not handler:
                http_logger.removeHandler(existing)
                try:
                    existing.close()
                except Exception:
                    pass

        if handler is not None and handler not in http_logger.handlers:
            http_logger.addHandler(handler)
            http_logger.propagate = False
            if http_logger.level == logging.NOTSET or http_logger.level > logging.INFO:
                http_logger.setLevel(logging.INFO)


def _suppress_http_logs() -> logging.Filter | None:
    suppress_enabled = _http_logs_are_suppressed()

    if not suppress_enabled:
        global _HTTP_SUPPRESSION_FILTER
        _HTTP_SUPPRESSION_FILTER = None
        if _HTTP_LOG_BASE_PATH is not None:
            _ensure_http_file_handler(_HTTP_LOG_BASE_PATH, _build_file_formatter())
        else:
            _configure_http_log_file_routing()
        return None

    _teardown_http_log_handler()

    filter_instance = _get_http_suppression_filter()

    for logger_name in _HTTP_LOGGER_NAMES:
        http_logger = logging.getLogger(logger_name)
        http_logger.propagate = False
        console_handlers = [h for h in http_logger.handlers if isinstance(h, logging.StreamHandler)]
        for handler in console_handlers:
            http_logger.removeHandler(handler)

    return filter_instance


def setup_logging(
    name: str,
    *,
    log_file: str | None = None,
    level: int | None = None,
    log_dir: str | None = None,
    maintenance: bool = False,
    console_stream: object | None = None,
) -> logging.Logger:
    with _LOGGING_LOCK:
        logger = logging.getLogger(name)

        resolved_level = level if level is not None else get_log_level()
        logger.setLevel(logging.DEBUG)

        log_directory = _resolve_log_dir(log_dir)
        log_path = _resolve_log_path(log_file, log_directory)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        service = os.getenv("SERVICE_NAME", "casino_calendar")
        environment = os.getenv("APP_ENV", os.getenv("ENV", "local"))

        http_filter = _suppress_http_logs()
        stream = console_stream if console_stream is not None else sys.stderr

        console_handler = _find_handler(logger, _CONSOLE_ROLE)
        if console_handler is None:
            console_handler = _build_console_handler(
                level=resolved_level,
                stream=stream,
                http_filter=http_filter,
                service=service,
                environment=environment,
            )
            setattr(console_handler, _HANDLER_ROLE_ATTR, _CONSOLE_ROLE)
            logger.addHandler(console_handler)
        else:
            console_handler.setLevel(resolved_level)
            _apply_filter(console_handler, http_filter)
            is_tty = hasattr(stream, "isatty") and bool(stream.isatty())
            if console_handler.__class__.__module__.startswith("rich.logging"):
                console_handler.setFormatter(ConsoleFormatter(use_colors=is_tty, use_rich_markup=True))
            elif _find_spec("colorlog") and console_handler.__class__.__module__.startswith("logging"):
                console_handler.setFormatter(_build_colorlog_formatter())
            else:
                console_handler.setFormatter(ConsoleFormatter(use_colors=is_tty, use_rich_markup=False))
            _ensure_context_filter(console_handler, service, environment)

        file_formatter = _build_file_formatter()
        filters: list[logging.Filter] = [_ContextFilter(service, environment)]

        minimal_filter = _MinimalTestFilter() if _should_apply_minimal_filter(log_path) else None
        if minimal_filter is not None:
            filters.append(minimal_filter)

        if maintenance:
            filters.append(_get_maintenance_filter())

        _ensure_timed_file_handler(
            logger,
            role=_FILE_ROLE if not maintenance else f"{_FILE_ROLE}_maintenance",
            log_path=log_path,
            level=logging.DEBUG,
            retention_days=14,
            formatter=file_formatter,
            filters=filters,
        )

        debug_path = _resolve_debug_log_path(log_directory, resolved_level)
        if debug_path is not None and debug_path != log_path:
            _ensure_timed_file_handler(
                logger,
                role=_DEBUG_FILE_ROLE,
                log_path=debug_path,
                level=logging.DEBUG,
                retention_days=7,
                formatter=file_formatter,
                filters=[_ContextFilter(service, environment)],
            )

        _ensure_http_file_handler(log_path, file_formatter)

        logger.propagate = False

        return logger


def get_context_logger(name: str, **context: str) -> ContextLoggerAdapter:
    logger = setup_logging(name)
    return ContextLoggerAdapter(logger, context)


__all__ = [
    "ContextLoggerAdapter",
    "ConsoleFormatter",
    "FileFormatter",
    "JsonLogFormatter",
    "get_context_logger",
    "get_log_level",
    "setup_logging",
]
