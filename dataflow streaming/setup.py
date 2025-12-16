import setuptools

REQUIRED_PACKAGES = [
    "db-dtypes",
    "apache-beam[gcp]",
    "google-cloud-bigquery",
    "google-cloud-aiplatform",
    "google-cloud-storage",
    "google-cloud-pubsub",
    "gcsfs",
    "fsspec",
    "pandas",
    "numpy",
    "scikit-learn",
    "protobuf"
    
]

PACKAGE_NAME = "ato_streaming_pipeline"
PACKAGE_VERSION = "0.0.1"

setuptools.setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description="ATO Fraud Detection Dataflow Streaming Pipeline Dependencies",
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
)
