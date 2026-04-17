import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

logger = logging.getLogger("wayfinder.telemetry")

_tracer_provider: TracerProvider | None = None


def setup_telemetry() -> None:
    global _tracer_provider

    service_name = os.getenv("OTEL_SERVICE_NAME", "wayfinder-supply-co")
    environment = os.getenv("DEPLOYMENT_ENV", "local")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        "deployment.environment": environment,
    })

    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        exporter = OTLPSpanExporter()  # reads OTEL_EXPORTER_OTLP_* env vars
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"OTel OTLP exporter configured → {endpoint}")
    else:
        logger.info("OTel running in no-export mode (OTEL_EXPORTER_OTLP_ENDPOINT not set)")

    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)
