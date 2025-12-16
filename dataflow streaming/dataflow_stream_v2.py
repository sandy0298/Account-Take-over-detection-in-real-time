
import json
import logging
import time
import pickle
from typing import Dict, Any

import numpy as np
import pandas as pd
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, SetupOptions
from apache_beam.pvalue import TaggedOutput

# Google Cloud SDK
from google.cloud import bigquery, aiplatform, storage

# --- CONFIG ---
PROJECT = "liquid-XXXXX-XXXXX-e3"
REGION = "us-central1"
GCS_BUCKET_NAME = "ato_dataflow"
JOB_NAME = "pubsub-to-vertexai-bq-v3"

INPUT_SUBSCRIPTION = "projects/liquid-XXXXX-XXXXX-e3/subscriptions/ato_capture-sub"
FRAUD_TOPIC = "projects/liquid-XXXXX-XXXXX-e3/topics/ato_fraud_capture"

HIST_DATASET = "ato_historical_Data"
HIST_TABLE = "customer_footprint_v1"
RESULT_TABLE_SPEC = f"{PROJECT}.{HIST_DATASET}.fraud_detection_results"

#twillio_end_point
ENDPOINT_ID = "186XXXXXXXX8000"

MAX_SEQUENCE_LENGTH = 128
MIN_HISTORY = 5

SCALER_PATH = "artifacts/scaler_params.pkl"
THRESHOLD_PATH = "artifacts/threshold.json"

FRAUD_TAG = "fraud_output"

logging.getLogger().setLevel(logging.INFO)


# ----------------------------------------------------------------------
# 1. Load Artifacts
# ----------------------------------------------------------------------
def load_artifacts():
    storage_client = storage.Client()

    # scaler + feature order
    scaler_blob = storage_client.bucket(GCS_BUCKET_NAME).blob(SCALER_PATH)
    scaler_params = pickle.loads(scaler_blob.download_as_bytes())
    scaler = scaler_params["scaler"]
    feature_order = scaler_params["feature_order"]

    # threshold
    threshold_blob = storage_client.bucket(GCS_BUCKET_NAME).blob(THRESHOLD_PATH)
    threshold = json.loads(threshold_blob.download_as_bytes())["threshold"]

    logging.info(f"Artifacts loaded. Threshold: {threshold}")
    return scaler, feature_order, float(threshold)


def format_for_bq_and_alert(element: Dict[str, Any]) -> Dict[str, Any]:
    row = element["raw_record"].copy()
    row["is_fraud"] = element["is_fraud"]
    row["reconstruction_error"] = element["reconstruction_error"]
    row["ingest_ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return row


def format_for_pubsub(record: Dict[str, Any]) -> bytes:
    return json.dumps(record).encode("utf-8")


# ----------------------------------------------------------------------
# 2. Build Sequence DoFn
# ----------------------------------------------------------------------
class BuildSequenceDoFn(beam.DoFn):

    def setup(self):
        self.bq_client = bigquery.Client(project=PROJECT)
        self.scaler, self.feature_order, _ = load_artifacts()
        logging.info("BuildSequenceDoFn setup complete.")

    def process(self, element: bytes):
        try:
            record = json.loads(element.decode("utf-8"))
        except:
            logging.exception("Could not decode Pub/Sub message")
            return

        user_id = record.get("user_id")
        if not user_id:
            logging.warning("Missing user_id — skipping.")
            return

        features_to_fetch = [f for f in self.feature_order if f not in ["is_fraud", "session_id"]]
        cols = ", ".join(features_to_fetch)

        query = f"""
            SELECT {cols}
            FROM `{PROJECT}.{HIST_DATASET}.{HIST_TABLE}`
            WHERE user_id = '{user_id}'
            ORDER BY day_of_week DESC, hour_of_day DESC
            LIMIT {MAX_SEQUENCE_LENGTH - 1}
        """

        try:
            df_hist = self.bq_client.query(query).to_dataframe()
        except:
            logging.exception(f"Failed BQ fetch for {user_id}")
            return

        new_row = [record.get(col, 0) for col in features_to_fetch]
        df_new = pd.DataFrame([new_row], columns=features_to_fetch)

        if len(df_hist) < MIN_HISTORY:
            pad_n = MIN_HISTORY - len(df_hist)
            padding_data = df_hist.iloc[0].values if not df_hist.empty else [0] * len(features_to_fetch)
            padding_df = pd.DataFrame([padding_data] * pad_n, columns=features_to_fetch)
            df_hist = pd.concat([padding_df, df_hist], ignore_index=True)

        df_hist = df_hist.tail(MAX_SEQUENCE_LENGTH - 1)
        df_sequence = pd.concat([df_hist, df_new], ignore_index=True)

        X = df_sequence.values.astype(float)
        mins = self.scaler.data_min_
        maxs = self.scaler.data_max_

        X_scaled = np.clip((X - mins) / (maxs - mins), 0, 1)
        X_scaled = X_scaled.reshape(1, len(df_sequence), len(df_sequence.columns))

        yield {
            "user_id": user_id,
            "sequence": X_scaled.tolist(),
            "raw_record": record
        }


# ----------------------------------------------------------------------
# 3. Fraud Detection DoFn (Vertex AI)
# ----------------------------------------------------------------------
class DetectFraudDoFn(beam.DoFn):

    def setup(self):
        aiplatform.init(project=PROJECT, location=REGION)
        self.endpoint = aiplatform.Endpoint(ENDPOINT_ID)
        _, _, self.threshold = load_artifacts()
        logging.info("DetectFraudDoFn setup done. Threshold loaded.")

    def process(self, element: Dict[str, Any]):
        try:
            seq = element["sequence"]
            prediction = self.endpoint.predict(instances=seq)
            recon = np.array(prediction.predictions[0])

            orig_last = np.array(seq)[0, -1, :]
            recon_last = recon[-1, :]

            mse = float(np.mean((orig_last - recon_last) ** 2))

            element["reconstruction_error"] = mse
            element["is_fraud"] = int(mse > self.threshold)
        except:
            logging.exception("Prediction error")
            element["reconstruction_error"] = None
            element["is_fraud"] = None
            return

        # Main output
        yield element

        # Tagged output if fraud
        if element["is_fraud"] == 1:
            yield TaggedOutput(FRAUD_TAG, element)


# ----------------------------------------------------------------------
# 4. Pipeline Execution
# ----------------------------------------------------------------------
def run():
    options = PipelineOptions([
        f"--runner=DataflowRunner",
        f"--project={PROJECT}",
        f"--region={REGION}",
        f"--job_name={JOB_NAME}",
        f"--temp_location=gs://{GCS_BUCKET_NAME}/temp",
        f"--staging_location=gs://{GCS_BUCKET_NAME}/staging",
        "--setup_file=./setup.py",
        "--disk_size_gb=50",
    ])

    options.view_as(StandardOptions).streaming = True
    options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=options) as p:

        pubsub_bytes = p | "ReadPubSub" >> beam.io.ReadFromPubSub(subscription=INPUT_SUBSCRIPTION)

        sequences = pubsub_bytes | "BuildSequence" >> beam.ParDo(BuildSequenceDoFn())

        # *** FIXED SIDE OUTPUT SYNTAX ***
        predictions_tuple = (
            sequences
            | "DetectFraud" >> beam.ParDo(DetectFraudDoFn())
                .with_outputs(FRAUD_TAG, main="all_records")
        )

        all_records = predictions_tuple.all_records
        fraud_records_stream = predictions_tuple[FRAUD_TAG]

        # BigQuery Sink (all records)
        (
            all_records
            | "FormatAllRecordsForBQ" >> beam.Map(format_for_bq_and_alert)
            | "WriteAllToBQ" >> beam.io.WriteToBigQuery(
                table=RESULT_TABLE_SPEC,
                method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

        # Fraud Pub/Sub Sink
        (
            fraud_records_stream
            | "FormatFraudForPubSub" >> beam.Map(format_for_bq_and_alert)
            | "FraudToBytes" >> beam.Map(format_for_pubsub)
            | "WriteFraudToPubSub" >> beam.io.WriteToPubSub(topic=FRAUD_TOPIC)
        )


if __name__ == "__main__":
    logging.info("Starting Dataflow pipeline...")
    run()
