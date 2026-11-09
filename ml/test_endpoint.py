import json
import boto3

rt = boto3.client("sagemaker-runtime", region_name="us-east-1")
r = rt.invoke_endpoint(
    EndpointName="cloudscale-category",
    ContentType="application/json",
    Accept="application/json",
    Body=json.dumps({"text": "black hp laptop charger"}),
)
print(r["Body"].read().decode())

