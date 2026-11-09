import io, urllib.parse
import boto3
from PIL import Image

s3 = boto3.client("s3")
MAX_SIZE = (300, 300)


def handler(event, context):
    for rec in event["Records"]:
        bucket = rec["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])
        if not key.startswith("uploads/"):
            continue
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        img = Image.open(io.BytesIO(body))
        fmt = img.format or "JPEG"
        img.thumbnail(MAX_SIZE)
        if fmt == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format=fmt)
        out.seek(0)
        thumb_key = "thumbs/" + key.split("/", 1)[1]
        s3.put_object(Bucket=bucket, Key=thumb_key, Body=out, ContentType=f"image/{fmt.lower()}")
    return {"ok": True}