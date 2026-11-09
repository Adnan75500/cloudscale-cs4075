import sys
import boto3
import sagemaker

from sagemaker.sklearn.model import SKLearnModel
from sagemaker.serverless import ServerlessInferenceConfig

if len(sys.argv) != 3:
    raise SystemExit(
        "Usage: python ml/deploy.py SAGEMAKER_ROLE_ARN ML_BUCKET"
    )

ROLE_ARN = sys.argv[1]
BUCKET = sys.argv[2]
REGION = "us-east-1"

boto_session = boto3.Session(region_name=REGION)

sess = sagemaker.Session(
    boto_session=boto_session,
    default_bucket=BUCKET
)

s3 = boto_session.client("s3")

# Upload existing trained model
s3.upload_file(
    "ml/model.tar.gz",
    BUCKET,
    "models/model.tar.gz"
)

model_data = f"s3://{BUCKET}/models/model.tar.gz"

# Create model using only the clean inference directory
model = SKLearnModel(
    model_data=model_data,
    role=ROLE_ARN,
    entry_point="inference.py",
    source_dir="ml/serving",
    framework_version="1.4-2",
    py_version="py3",
    env={
        "PYTHONPATH": "/opt/ml/model/code:/home/model-server/.local/lib/python3.10/site-packages:/root/.local/lib/python3.10/site-packages:/opt/ml/code"
    },
    sagemaker_session=sess,
)

# Deploy serverless endpoint
predictor = model.deploy(
    serverless_inference_config=ServerlessInferenceConfig(
        memory_size_in_mb=2048,
        max_concurrency=2
    ),
    endpoint_name="cloudscale-category"
)

print("Endpoint deployment requested: cloudscale-category")