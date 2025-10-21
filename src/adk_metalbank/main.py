# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uvicorn
import logging
import google.auth
import google.auth.transport.requests
import grpc
from google.adk.cli.fast_api import get_fast_api_app
from fastapi import FastAPI
from src.adk_metalbank.config import set_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load application-specific configurations (e.g., environment variables).
set_config()

# Define the directory where agent configurations are located.
AGENT_DIR = f"{os.path.dirname(os.path.abspath(__file__))}"
# Define allowed origins for Cross-Origin Resource Sharing (CORS).
ALLOWED_ORIGINS = ["http://localhost", "*"]



# --- FastAPI Application Initialization ---
# Create the FastAPI application instance using the ADK's helper function.
# This function discovers and loads agent definitions from the specified directory
# and sets up the necessary API endpoints.
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=True,
)

def setup_opentelemetry() -> None:
    """
    Configures OpenTelemetry to export traces, logs, and metrics to Google Cloud.
    This setup is crucial for observing the application's behavior, especially
    for tracing Generative AI interactions.
    """
    from google.auth.transport.grpc import AuthMetadataPlugin
    from opentelemetry import _events as events, _logs as logs, metrics, trace
    from opentelemetry.exporter.cloud_logging import CloudLoggingExporter
    from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.google_genai import GoogleGenAiSdkInstrumentor
    from opentelemetry.sdk._events import EventLoggerProvider
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.google_genai import GoogleGenAiSdkInstrumentor

    # --- Google Cloud Platform Scopes ---
    # Define the necessary OAuth 2.0 scopes for Google Cloud services.
    # These scopes grant the application permission to send data to Cloud Trace,
    # Logging, and Monitoring, which are essential for observability.
    GCP_SCOPES = [
        "https://www.googleapis.com/auth/trace.append",       # For Cloud Trace
        "https://www.googleapis.com/auth/logging.write",      # For Cloud Logging
        "https://www.googleapis.com/auth/monitoring.write",   # For Cloud Monitoring
        "https://www.googleapis.com/auth/cloud-platform",     # Broad scope for other Google ADK/AI Platform needs
    ]


    # Authenticate and get the project ID using Application Default Credentials (ADC).
    credentials, project_id = google.auth.default(scopes=GCP_SCOPES)
    # Create a resource identifier for this service instance, which helps in
    # associating telemetry data with the correct application in Google Cloud.
    resource = Resource.create(
        attributes={
            SERVICE_INSTANCE_ID: f"worker-{os.getpid()}",
            "gcp.project_id": project_id,
        }
    )
    # Set up OTLP auth
    # Create an authentication plugin for gRPC channels to securely send
    # telemetry data to the Google Cloud backend.
    request = google.auth.transport.requests.Request()
    auth_metadata_plugin = AuthMetadataPlugin(credentials=credentials, request=request)

    # Combine SSL credentials with the auth plugin for a secure gRPC channel.
    channel_creds = grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(auth_metadata_plugin),
    )

    # --- Trace Provider Setup ---
    tracer_provider = TracerProvider(resource=resource)
    # The BatchSpanProcessor groups spans together before sending them to the exporter.
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                credentials=channel_creds,
                endpoint="https://telemetry.googleapis.com:443/v1/traces",
            )
        )
    )
    # Register the tracer provider globally.
    trace.set_tracer_provider(tracer_provider)

    # --- Logger Provider Setup ---
    logger_provider = LoggerProvider(resource=resource)
    # The BatchLogRecordProcessor groups log records for efficient export to Cloud Logging.
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(CloudLoggingExporter())
    )
    # Register the logger provider globally.
    logs.set_logger_provider(logger_provider)

    # --- Event Logger Provider Setup ---
    event_logger_provider = EventLoggerProvider(logger_provider)
    events.set_event_logger_provider(event_logger_provider)

    # --- Meter (Metrics) Provider Setup ---
    # The PeriodicExportingMetricReader exports metrics to Cloud Monitoring at regular intervals.
    reader = PeriodicExportingMetricReader(CloudMonitoringMetricsExporter(
        project_id=project_id,
    ))
    meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
    # Register the meter provider globally.
    metrics.set_meter_provider(meter_provider)

    # --- Auto-instrumentation ---
    # This automatically patches the `google-genai` library to create trace spans
    # for each call to the Generative AI model, providing deep visibility.
    GoogleGenAiSdkInstrumentor().instrument()
    return

# Conditionally enable OpenTelemetry based on an environment variable.
# This allows developers to turn on detailed GenAI tracing when needed.
if os.getenv("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false").lower() == "true":
    setup_opentelemetry()

if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))