import os, uuid, secrets, datetime
import json
from functools import wraps
from urllib.parse import urlencode

import boto3, jwt, requests
from flask import Flask, request, session, redirect, render_template, abort, jsonify

REGION = os.environ["AWS_REGION"]

QUEUE_URL = os.environ["QUEUE_URL"]
TOPIC_ARN = os.environ["TOPIC_ARN"]

sqs = boto3.client("sqs", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)
SM_ENDPOINT = os.environ["SM_ENDPOINT"]
smrt = boto3.client("sagemaker-runtime", region_name=REGION)
BEDROCK_MODEL = os.environ["BEDROCK_MODEL"]
brt = boto3.client("bedrock-runtime", region_name=REGION)
TABLE = os.environ["TABLE_NAME"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]
CDN = os.environ["CDN_DOMAIN"]
COGNITO_DOMAIN = os.environ["COGNITO_DOMAIN"]
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
POOL_ID = os.environ["COGNITO_POOL_ID"]
APP_URL = os.environ["APP_URL"]

ssm = boto3.client("ssm", region_name=REGION)
table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)
s3 = boto3.client("s3", region_name=REGION)

app = Flask(__name__)
app.secret_key = ssm.get_parameter(Name=os.environ["SECRET_PARAM"], WithDecryption=True)["Parameter"]["Value"]
app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}"
jwks = jwt.PyJWKClient(f"{ISSUER}/.well-known/jwks.json")


def current_user():
    return session.get("user")


@app.context_processor
def inject():
    return {"user": current_user(), "cdn": CDN}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            session["next"] = request.path
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


@app.get("/health")
def health():
    return "ok"


@app.get("/burn")
def burn():
    return str(sum(i * i for i in range(2_000_000)))


# ---------- auth ----------
@app.get("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["state"] = state
    q = urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email",
        "redirect_uri": f"{APP_URL}/callback",
        "state": state,
    })
    return redirect(f"{COGNITO_DOMAIN}/login?{q}")


@app.get("/callback")
def callback():
    expected = session.pop("state", None)
    if not expected or request.args.get("state") != expected or "code" not in request.args:
        abort(400)
    r = requests.post(f"{COGNITO_DOMAIN}/oauth2/token", data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": request.args["code"],
        "redirect_uri": f"{APP_URL}/callback",
    }, timeout=10)
    if r.status_code != 200:
        abort(400)
    id_token = r.json()["id_token"]
    key = jwks.get_signing_key_from_jwt(id_token).key
    claims = jwt.decode(id_token, key, algorithms=["RS256"], audience=CLIENT_ID, issuer=ISSUER)
    session["user"] = {"sub": claims["sub"], "email": claims.get("email", "")}
    return redirect(session.pop("next", "/"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(f"{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={APP_URL}/")


# ---------- listings ----------
@app.get("/")
def index():
    items = table.scan(Limit=200).get("Items", [])
    q = request.args.get("q", "").lower()
    if q:
        items = [i for i in items if q in (i.get("title", "") + " " + i.get("description", "")).lower()]
    items.sort(key=lambda i: i.get("created_at", ""), reverse=True)
    return render_template("index.html", items=items, q=q)


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "GET":
        return render_template("new.html")
    user = current_user()
    lid = uuid.uuid4().hex
    photo_key = thumb_key = ""
    photo = request.files.get("photo")
    if photo and photo.filename:
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png"):
            abort(400, "Only jpg or png images")
        photo_key = f"uploads/{lid}.{ext}"
        thumb_key = f"thumbs/{lid}.{ext}"
        s3.upload_fileobj(photo, MEDIA_BUCKET, photo_key, ExtraArgs={"ContentType": photo.mimetype})
    table.put_item(Item={
        "listing_id": lid,
        "owner_sub": user["sub"],
        "owner_email": user["email"],
        "kind": request.form.get("kind", "lost"),
        "title": request.form["title"][:120],
        "description": request.form.get("description", "")[:1000],
        "category": request.form.get("category", "other"),
        "status": "open",
        "photo_key": photo_key,
        "thumb_key": thumb_key,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "responses": [],
    })
    try:
        sns.subscribe(
            TopicArn=TOPIC_ARN,
            Protocol="email",
            Endpoint=user["email"],
            Attributes={
                "FilterPolicy": json.dumps({
                    "owner_email": [user["email"]]
                })
            },
        )
    except Exception as e:
        app.logger.warning("sns subscribe failed: %s", e)
    return redirect(f"/listing/{lid}")


@app.get("/listing/<lid>")
def listing(lid):
    item = table.get_item(Key={"listing_id": lid}).get("Item")
    if not item:
        abort(404)
    return render_template("listing.html", i=item)

@app.post("/listing/<lid>/respond")
@login_required
def respond(lid):
    item = table.get_item(Key={"listing_id": lid}).get("Item")

    if not item:
        abort(404)

    user = current_user()
    msg = request.form["message"][:500]

    resp = {
        "from": user["email"],
        "message": msg,
        "at": datetime.datetime.utcnow().isoformat()
    }

    table.update_item(
        Key={"listing_id": lid},
        UpdateExpression="SET responses = list_append(if_not_exists(responses, :empty), :r)",
        ExpressionAttributeValues={
            ":r": [resp],
            ":empty": []
        },
    )

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "title": item["title"],
            "owner_email": item["owner_email"],
            "responder_email": user["email"],
            "message": msg,
            "url": f"{APP_URL}/listing/{lid}",
        })
    )

    return redirect(f"/listing/{lid}")


@app.post("/api/suggest-category")
@login_required
def suggest_category():
    text = request.get_json(force=True).get("text", "")[:500]
    try:
        r = smrt.invoke_endpoint(
            EndpointName=SM_ENDPOINT,
            ContentType="application/json",
            Accept="application/json",
            Body=json.dumps({"text": text}),
        )
        return jsonify(json.loads(r["Body"].read()))
    except Exception as e:
        app.logger.error("sagemaker call failed: %s", e)
        return jsonify({"error": "Category model is unavailable right now"}), 503


@app.post("/api/write-description")
@login_required
def write_description():
    d = request.get_json(force=True)
    prompt = (
        "Write a clear, friendly description of 2 to 3 sentences for a campus "
        + str(d.get("kind", "lost"))[:10] + "-and-found listing. "
        "Item: " + str(d.get("title", ""))[:120] + ". "
        "Category: " + str(d.get("category", ""))[:30] + ". "
        "Extra details from the user: " + str(d.get("notes", ""))[:300] + ". "
        "Only use the details given. Do not invent details and do not include contact information."
    )
    try:
        r = brt.converse(
            modelId=BEDROCK_MODEL,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 200, "temperature": 0.4},
        )
        text = r["output"]["message"]["content"][0]["text"].strip()
        return jsonify({"description": text})
    except Exception as e:
        app.logger.error("bedrock call failed: %s", e)
        return jsonify({"error": "Description generator is unavailable right now"}), 503

