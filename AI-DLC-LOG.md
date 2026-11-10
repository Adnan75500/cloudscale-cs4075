# AI-DLC Development Log

## Phase 1: Networking & Security Perimeter

**Inception (2026-11-08):**
- Prompt given to the agent: Design a custom AWS VPC using `10.0.0.0/16`, with two public and two private subnets across two Availability Zones (`us-east-1a`, `us-east-1b`).
- Requirements produced: Internet Gateway, a cost-effective NAT instance for private-subnet internet egress, chained security groups (ALB SG allowing CloudFront prefix list; App SG accepting port 8000 only from ALB SG), and VPC Gateway Endpoints for S3 and DynamoDB.
- Questions asked: Should we use AWS NAT Gateway or an EC2 NAT instance to minimize student budget consumption?
- Answers: Use a `t3.micro` EC2 NAT instance with iptables masquerading and free VPC Gateway Endpoints to save ~$32/month.

**Construction (2026-11-08):**
- Plan proposed by the agent: Terraform configuration in `terraform/network.tf` and `terraform/nat_userdata.sh`.
- What we reviewed: Security group rules, route tables, and subnet CIDR blocks (`10.0.0.0/24`, `10.0.1.0/24`, `10.0.10.0/24`, `10.0.11.0/24`).
- What we changed or rejected: AWS rejected `t3.nano` because it was not Free Tier eligible in the account/region. Replaced with `t3.micro` for Free Tier eligibility.
- What we approved and applied: Ran `terraform apply` creating 18 network resources.

**Operations (2026-11-08):**
- What was actually built: Custom VPC (`cloudscale-vpc`), 4 subnets, IGW, public/private route tables, NAT instance (`cloudscale-nat`), S3 and DynamoDB VPC Gateway Endpoints.
- AWS resource names: `vpc-0a236cc8d275c1998`, `i-07011ea789f248672`, `cloudscale-s3-endpoint`, `cloudscale-dynamodb-endpoint`.
- Issues found: None; verified private route table directs `0.0.0.0/0` to NAT network interface while S3/DynamoDB prefix lists target gateway endpoints.
- Decisions to remember: Keep all application servers in private subnets with no public IPs.

**Commit:** `5d2ac7a`

---

## Phase 2: Compute, Load Balancing & Auto Scaling

**Inception (2026-11-08):**
- Prompt given to the agent: Configure an Application Load Balancer in public subnets, an Auto Scaling Group in private subnets, and CloudFront distribution for HTTPS edge termination.
- Requirements produced: Launch template on Amazon Linux 2023 with Python 3.11, Gunicorn systemd unit, `/health` endpoint checks, ASG capacity (min 2, desired 2, max 4, `t3.micro`), and TargetTrackingScaling on average CPU > 50%.
- Questions asked: How should HTTPS be terminated without purchasing a custom domain?
- Answers: Use Amazon CloudFront with its default `*.cloudfront.net` SSL/TLS certificate forwarding to the ALB over HTTP.

**Construction (2026-11-08):**
- Plan proposed by the agent: Authored `terraform/compute.tf` and `terraform/cdn.tf`.
- What we reviewed: Target group health check path (`/health`), deregistration delay (30s), launch template IAM instance profile, and IMDSv2 configuration.
- What we changed or rejected: Strictly rejected opening SSH port 22 to the public internet; enforced AWS Systems Manager Session Manager for all remote management. Enforced `http_tokens = "required"` (IMDSv2).
- What we approved and applied: Applied Terraform plan for ALB, ASG, Launch Template, and CloudFront distribution.

**Operations (2026-11-08):**
- What was actually built: ALB (`cloudscale-alb`), Target Group (`cloudscale-tg`), ASG (`cloudscale-asg`), Launch Template, and CloudFront Distribution.
- AWS resource names: `cloudscale-alb`, `cloudscale-tg`, `cloudscale-asg`, `d2oszhh0246ohl.cloudfront.net`.
- Issues found: Initial instance boot required dependency install before turning healthy; tuned ALB health check intervals to 15s.
- Decisions to remember: ASG spans both private subnets for multi-AZ high availability.

**Commit:** `9cd2769`

---

## Phase 3: Storage (S3) & Media CDN

**Inception (2026-11-08):**
- Prompt given to the agent: Create a secure, private S3 media bucket for user item photos with lifecycle cost management and CloudFront Origin Access Control (OAC).
- Requirements produced: S3 bucket `cloudscale-media-<account_id>`, block all public access, versioning enabled, lifecycle transition to Standard-IA after 30 days, expiration of noncurrent versions after 90 days, CloudFront distribution with OAC.
- Questions asked: Should users directly access S3 or only CloudFront?
- Answers: 100% private S3 with bucket policy restricting `s3:GetObject` strictly to the CloudFront distribution ARN via OAC.

**Construction (2026-11-08):**
- Plan proposed by the agent: Authored `terraform/storage.tf` with `aws_s3_bucket`, `aws_s3_bucket_lifecycle_configuration`, `aws_cloudfront_origin_access_control`, and bucket policy.
- What we reviewed: Public Access Block settings and IAM scoping for EC2 role to `PutObject` only on `uploads/*`.
- What we changed or rejected: Blocked direct public read access on S3; enforced `AWS:SourceArn` condition on CloudFront distribution.
- What we approved and applied: Ran `terraform apply` to create the media bucket and media CDN distribution.

**Operations (2026-11-08):**
- What was actually built: S3 media bucket with versioning and lifecycle rules, OAC, and CloudFront media distribution.
- AWS resource names: `cloudscale-media-764277693415`, `cloudscale-media-oac`.
- Issues found: Direct curl to S3 returned HTTP 403 (expected); retrieval via CloudFront returned HTTP 200.
- Decisions to remember: Photos in `uploads/` trigger Lambda thumbnail generation; thumbnails are served from `thumbs/`.

**Commit:** `fb7aba8`

---

## Phase 4: Data Layer (Amazon DynamoDB)

**Inception (2026-11-08):**
- Prompt given to the agent: Design the NoSQL database for lost-and-found listings and response threads.
- Requirements produced: DynamoDB table with partition key `listing_id` (String), on-demand billing mode (`PAY_PER_REQUEST`), and EC2 IAM permissions scoped strictly to table ARN.
- Questions asked: Relational database (RDS PostgreSQL) vs DynamoDB NoSQL?
- Answers: DynamoDB is serverless, zero idle cost, scales automatically, and perfectly handles semi-structured lost-and-found metadata.

**Construction (2026-11-08):**
- Plan proposed by the agent: Authored `terraform/data.tf` creating `cloudscale-listings` and attached IAM policy to EC2 role.
- What we reviewed: IAM actions granted: `PutItem`, `GetItem`, `UpdateItem`, `Scan`, `DeleteItem`.
- What we changed or rejected: Scoped `Resource` strictly to `aws_dynamodb_table.listings.arn` rather than `*`.
- What we approved and applied: Applied Terraform to provision the DynamoDB table.

**Operations (2026-11-08):**
- What was actually built: DynamoDB table `cloudscale-listings` in on-demand mode.
- AWS resource names: `cloudscale-listings`.
- Issues found: Verified that EC2 instances query DynamoDB through the VPC Gateway Endpoint with zero NAT data transfer charges.
- Decisions to remember: Responses are stored as an attribute list within the listing item.

**Commit:** `3484027`

---

## Phase 5: Identity & Access (Amazon Cognito)

**Inception (2026-11-08):**
- Prompt given to the agent: Implement secure user registration, email verification, and login using Amazon Cognito.
- Requirements produced: Cognito User Pool with self-service sign-up, verification code via email, Hosted UI domain, and public client configured with OAuth 2.0 authorization code flow.
- Questions asked: Should the app client use a client secret?
- Answers: Use a public app client (no secret) because the Flask app runs on EC2 instances provisioned via user-data, avoiding secret exposure.

**Construction (2026-11-08):**
- Plan proposed by the agent: Authored `terraform/auth.tf` defining `cloudscale-users`, user pool client, and domain prefix.
- What we reviewed: Callback URLs (`https://d2oszhh0246ohl.cloudfront.net/callback`) and Logout URLs (`https://d2oszhh0246ohl.cloudfront.net/`).
- What we changed or rejected: Verified scopes restricted to `openid` and `email`.
- What we approved and applied: Applied Terraform to provision the Cognito User Pool and domain.

**Operations (2026-11-08):**
- What was actually built: Cognito User Pool (`cloudscale-users`), Hosted UI domain, and OAuth 2.0 client.
- AWS resource names: User Pool `us-east-1_eXample`, Client `cloudscale-web`.
- Issues found: Tested sign-up and email verification; confirmation codes delivered promptly to student inbox.
- Decisions to remember: Token verification validates JWT signatures against Cognito's public JWKS endpoint.

**Commit:** `6e5ff98`

---

## Phase 6: Web Application Architecture (Flask)

**Inception (2026-11-08):**
- Prompt given to the agent: Build a production Flask application with lost-and-found item posting, photo uploads, search filtering, and DynamoDB persistence.
- Requirements produced: Flask backend in `app/app.py`, Jinja2 HTML templates, session management using SSM Parameter Store secret key, and Gunicorn systemd service.
- Questions asked: How to maintain session persistence across multiple EC2 instances behind the ALB?
- Answers: Store the Flask `SECRET_KEY` in AWS SSM Parameter Store (`/cloudscale/flask-secret-key`) so all instances sign and verify session cookies identically without sticky sessions.

**Construction (2026-11-08):**
- Plan proposed by the agent: Created `app/app.py`, `app/templates/`, `app/static/`, and packaging script `build_app.py`.
- What we reviewed: Secure session cookies (`HttpOnly`, `Secure`, `SameSite=Lax`), CSRF protection, and error handling.
- What we changed or rejected: Rejected hardcoding configuration; rendered `/etc/app.env` dynamically via Terraform template.
- What we approved and applied: Deployed application package to S3 and updated ASG instances.

**Operations (2026-11-08):**
- What was actually built: Modular Flask web app running under Gunicorn (2 worker processes).
- AWS resource names: SSM parameter `/cloudscale/flask-secret-key`, S3 asset bucket `cloudscale-code-*`.
- Issues found: Verified listings render in responsive grid; photos upload to S3 `uploads/` successfully.
- Decisions to remember: All user-facing routes are accessible via CloudFront edge URL.

**Commit:** `1c83dd4`

---

## Phase 7: Asynchronous Serverless (Lambda, SQS, SNS)

**Inception (2026-11-08):**
- Prompt given to the agent: Decouple slow photo thumbnail processing and email notifications using serverless AWS primitives.
- Requirements produced: Lambda #1 (Thumbnail) triggered by S3 `uploads/` to write resized 300px JPEG to `thumbs/`; SQS queue `cloudscale-responses` with Dead-Letter Queue (DLQ); Lambda #2 (Notifier) consuming SQS and publishing to SNS topic `cloudscale-response-notifications`.
- Questions asked: How to prevent an infinite Lambda invocation loop when writing thumbnails back to S3?
- Answers: Separate S3 prefix triggers strictly: trigger only on `uploads/*` and write output to `thumbs/*`.

**Construction (2026-11-08):**
- Plan proposed by the agent: Authored `terraform/serverless.tf`, `lambda/thumbnail.py`, and `lambda/notifier.py`.
- What we reviewed: Pillow Lambda layer compatibility (`manylinux2014_x86_64`), SQS message retention (4 days), and max receive count (3).
- What we changed or rejected: Scoped SNS publish permissions strictly to the notification topic ARN. Added SNS subscription filter policy.
- What we approved and applied: Applied Terraform to deploy Lambdas, SQS queues, and SNS topic.

**Operations (2026-11-08):**
- What was actually built: Two Lambda functions, Pillow layer, SQS queue with DLQ, and SNS topic.
- AWS resource names: `cloudscale-thumbnail`, `cloudscale-notifier`, `cloudscale-responses`, `cloudscale-responses-dlq`, `cloudscale-response-notifications`.
- Issues found: Lambda thumbnail execution verified in CloudWatch logs; SQS retries tested by simulating transient errors.
- Decisions to remember: Asynchronous decoupling keeps web request response time sub-100ms.

**Commit:** `1191d8b`

---

## Phase 8: Monitoring, Telemetry & Budget Controls

**Inception (2026-11-09):**
- Prompt given to the agent: Build unified CloudWatch observability, automated alarms, and budget cost controls.
- Requirements produced: CloudWatch dashboard `cloudscale` tracking EC2 CPU, ALB RequestCount, TargetResponseTime, HealthyHostCount, and Lambda invocations/errors; High CPU alarm (>70%) and ALB 5XX alarm (>=5); AWS Budget alert at $100.
- Questions asked: What thresholds prevent false alarms during normal development?
- Answers: Require 3 consecutive evaluation periods (60s) for CPU > 70% before sounding alarm.

**Construction (2026-11-09):**
- Plan proposed by the agent: Authored `terraform/monitoring.tf` defining dashboard widgets, alarms, and SNS alert topic.
- What we reviewed: Metric dimensions (ASG name, TargetGroup ARN, LoadBalancer ARN).
- What we changed or rejected: Configured budget notification thresholds at 50% actual, 80% actual, and 100% forecasted spend.
- What we approved and applied: Ran `terraform apply` creating monitoring dashboard and alarms.

**Operations (2026-11-09):**
- What was actually built: CloudWatch Dashboard `cloudscale`, 2 CloudWatch metric alarms, SNS alert topic `cloudscale-alerts`, and AWS Budget `cloudscale-credit`.
- AWS resource names: `cloudscale` (dashboard), `cloudscale-high-cpu`, `cloudscale-alb-5xx`, `cloudscale-alerts`.
- Issues found: Confirmed email subscription to SNS topic; manually tested alarm state and verified email receipt in inbox.
- Decisions to remember: Dashboard provides end-to-end SLA visibility across all 3 tiers.

**Commit:** `025fb88`

---

## Phase 9: Machine Learning (Amazon SageMaker)

**Inception (2026-11-09):**
- Prompt given to the agent: Train a lightweight scikit-learn text classifier on synthetic campus lost-and-found listings, deploy as a serverless SageMaker inference endpoint (`cloudscale-category`), and call it via the web app.
- Requirements produced: Least-privilege IAM role for SageMaker, training script with TF-IDF + LogisticRegression, serverless endpoint deployment script, and an in-app button to suggest categories.
- Questions asked: Real-time instance vs Serverless inference?
- Answers: Serverless inference scales to zero instances when idle, incurring $0 baseline cost while active 24/7.

**Construction (2026-11-09):**
- Plan proposed by the agent: Authored `terraform/ml.tf` defining `cloudscale-sagemaker-role` and `cloudscale-ml-<account_id>` S3 bucket.
- What we reviewed: Created `ml/data.csv` (synthetic titles categorized into 7 classes). Trained model using `ml/train.py` with scikit-learn 1.4.2 and numpy 1.26.4, exporting `model.joblib`. Authored serving handler in `ml/serving/inference.py`. Packaged model archive `ml/model.tar.gz`.
- What we changed or rejected: Resolved SageMaker container startup issue where `PYTHONPATH` needed to resolve `/opt/ml/model/code`, `/home/model-server/.local/lib/python3.10/site-packages`, and `/opt/ml/code`.
- What we approved and applied: Deployed endpoint using `ml/deploy.py` with `ServerlessInferenceConfig` (2048 MB memory, max concurrency 2).

**Operations (2026-11-10):**
- What was actually built: SageMaker Serverless Inference Endpoint `cloudscale-category` and model bucket.
- AWS resource names: `cloudscale-category`, `cloudscale-sagemaker-role`, `cloudscale-ml-764277693415`.
- Issues found: Endpoint verified `InService`; `ml/test_endpoint.py` returned predictions in ~360ms. Added `/api/suggest-category` to `app/app.py` and UI button in `app/templates/new.html`.
- Decisions to remember: Supervised classification ensures consistent taxonomy across campus lost items.

**Commit:** `a57c4b5`

---

## Phase 10: Generative AI (Amazon Bedrock)

**Inception (2026-11-10):**
- Prompt given to the agent: Use AWS Bedrock foundation model (`amazon.nova-lite-v1:0`) via Bedrock Converse API to generate factual 2-3 sentence listing descriptions from user notes.
- Requirements produced: Restrict EC2 role to `bedrock:InvokeModel` on the foundation model, provide `/api/write-description` in Flask, and connect to "Write description" UI button.
- Questions asked: How to prevent hallucinations and prompt injection?
- Answers: Use a strict system prompt instructing Nova Lite to stick solely to user-provided facts and reject prompt injections or contact information requests.

**Construction (2026-11-10):**
- Plan proposed by the agent: Verified access to `amazon.nova-lite-v1:0` in `us-east-1` using Bedrock Converse API.
- What we reviewed: Updated `terraform/compute.tf` with `bedrock:InvokeModel` on `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0`.
- What we changed or rejected: Added temperature=0.4 and maxTokens=200 for concise, factual descriptions.
- What we approved and applied: Rebuilt `build/app.zip`, applied Terraform, and started ASG rolling instance refresh on `cloudscale-asg`.

**Operations (2026-11-10):**
- What was actually built: Bedrock Converse API integration in Flask backend.
- AWS resource names: `amazon.nova-lite-v1:0`.
- Issues found: Verified that clicking "Write description" auto-drafts clean, helpful descriptions directly into the form.
- Decisions to remember: Nova Lite is fast, cost-effective, and fully supported via Converse API.

**Commit:** `a57c4b5`
