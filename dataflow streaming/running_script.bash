python -m dataflow_stream_v2 \
  --runner=DataflowRunner \
  --project=liquid-anchor-478906-e3 \
  --region=us-central1 \
  --temp_location=gs://ato_dataflow/temp \
  --staging_location=gs://ato_dataflow/staging \
  --job_name=pubsub-to-vertexai-bq-v3-$(date +%Y%m%d%H%M%S) \
  --disk_size_gb=50 \
  --streaming \
  --setup_file=./setup.py

