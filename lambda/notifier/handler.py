import json, os
import boto3

sns = boto3.client("sns")
TOPIC_ARN = os.environ["TOPIC_ARN"]


def handler(event, context):
    for rec in event["Records"]:
        m = json.loads(rec["body"])
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=("Someone responded to: " + m["title"])[:99],
            Message=m["responder_email"] + " wrote:\n\n" + m["message"] + "\n\nView: " + m["url"],
            MessageAttributes={"owner_email": {"DataType": "String", "StringValue": m["owner_email"]}},
        )