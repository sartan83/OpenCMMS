import os


_configured = False


def configure_telemetry(service_name: str) -> None:
    global _configured
    endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')
    if not endpoint or _configured:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.django import DjangoInstrumentor
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(
        resource=Resource.create({'service.name': service_name}),
    )
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    )
    trace.set_tracer_provider(provider)
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    _configured = True
