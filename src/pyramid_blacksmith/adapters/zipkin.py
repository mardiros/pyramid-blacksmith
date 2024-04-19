from typing import Any, Dict, Optional

from blacksmith import AbstractTraceContext
from zipkin import api  # type: ignore
from zipkin.models import Annotation  # type: ignore
from zipkin.util import hex_str  # type: ignore


class TraceContext(AbstractTraceContext):
    """
    Interface of the trace context for the middleware.

    See examples with starlette-zipking for an implementation.
    """

    @classmethod
    def make_headers(cls) -> Dict[str, str]:
        """Build headers for the sub requests."""
        trace = api.get_current_trace()
        if trace:
            ret = {
                "X-B3-TraceId": hex_str(trace.trace_id),
                "X-B3-SpanId": hex_str(trace.span_id),
            }
            if trace.parent_span_id:
                ret["X-B3-ParentSpanId"] = hex_str(trace.parent_span_id)
            return ret
        return {}

    def __init__(self, name: str, kind: str = "SERVER") -> None:
        """Create a trace span for the current context."""
        self.trace_factory = api.Trace(name)
        self.trace = None
        self.kind = kind.lower()

    def tag(self, key: str, value: str) -> "AbstractTraceContext":
        """Tag the span"""
        if self.trace is not None:
            self.trace.record(Annotation.string(key, value))
        return self

    def annotate(
        self, value: Optional[str], ts: Optional[float] = None
    ) -> "AbstractTraceContext":
        """Annotate the span"""
        if self.trace is not None:
            self.trace.record(Annotation.timestamp(value, ts))
        return self

    def __enter__(self) -> "AbstractTraceContext":
        """Make the created trace span of the current context the active span."""
        self.trace_factory.__enter__()
        self.trace = self.trace_factory.trace
        if self.trace:
            self.trace.record(Annotation.string("span.kind", self.kind))
        return self

    def __exit__(self, *exc: Any) -> None:
        """
        Ends the created trace span of the context, it parents become the active span.
        """
        self.trace_factory.__exit__(*exc)
