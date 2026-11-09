
# AI-DLC Development Log

## Phase 1: Project Setup

**Inception** (date):
- Prompt given to the agent:
- Requirements produced:
- Questions asked by the agent:
- Our answers:

**Construction** (date):
- Plan proposed by the agent:
- What we reviewed:
- What we changed or rejected:
- What we approved and applied:

**Operations** (date):
- What was actually built:
- AWS resource names:
- Issues found:
- Decisions to remember:

**Commit:** <commit hash or PR link>

---

## Phase 2: Infrastructure Development

**Inception** (date):
- Prompt given to the agent:
- Requirements produced:
- Questions asked by the agent:
- Our answers:

**Construction** (date):
- Plan proposed by the agent:
- What we reviewed:
- What we changed or rejected:
- What we approved and applied:

**Operations** (date):
- What was actually built:
- AWS resource names:
- Issues found:
- Decisions to remember:

**Commit:** <commit hash or PR link>
## Phase 1: Networking

**Inception (2026-11-08):**
- Prompted the AI-DLC agent to design a custom AWS VPC using `10.0.0.0/16`, with two public and two private subnets across two Availability Zones.
- Required an internet gateway, a NAT instance for private-subnet internet access, chained security groups, and S3 and DynamoDB gateway endpoints.
- Reviewed the proposed architecture before deploying resources.

**Construction (2026-11-08):**
- Created Terraform configuration in `terraform/providers.tf` and `terraform/network.tf`.
- Created `terraform/nat_userdata.sh` to configure IP forwarding and NAT masquerading on the NAT instance.
- Ran `terraform init`, `terraform fmt`, `terraform validate`, and `terraform plan`.
- Reviewed the initial plan: 18 resources to add, zero to change, and zero to destroy.
- AWS rejected `t3.nano` because it was not eligible for Free Tier in the selected account/region. Changed the NAT instance type to `t3.micro`, which AWS reported as Free Tier eligible.
- Revalidated and reviewed the revised plan: 6 resources to add, zero to change, and zero to destroy.

**Operations (2026-11-08):**
- Successfully deployed all 18 planned resources across two Terraform apply operations.
- VPC ID: `vpc-0a236cc8d275c1998`
- NAT instance ID: `i-07011ea789f248672`
- Created two public subnets, two private subnets, an internet gateway, public and private route tables, three security groups, a NAT instance, and S3 and DynamoDB gateway endpoints.
- Private-subnet internet connectivity and NAT user-data execution still need to be tested in the next phase.
- Cost consideration: `t3.micro` and its public IPv4 address may incur charges depending on account eligibility and usage. Monitor AWS Billing and Free Tier usage.

**Commit:** Pending

---

## Phase 9: SageMaker (Suggest Item Category)

**Inception (2026-11-09):**
- Goal: Train a lightweight scikit-learn text classifier on synthetic campus lost-and-found listings, deploy as a serverless SageMaker inference endpoint (`cloudscale-category`), and call it via the web app.
- Requirements: Least-privilege IAM role for SageMaker, training script with TF-IDF + LogisticRegression, serverless endpoint deployment script, and an in-app button to suggest categories.

**Construction (2026-11-09):**
- Authored `terraform/ml.tf` defining `cloudscale-sagemaker-role` and `cloudscale-ml-<account_id>` S3 bucket.
- Created `ml/data.csv` (synthetic titles categorized into 7 classes).
- Trained model using `ml/train.py` with scikit-learn 1.4.2 and numpy 1.26.4, exporting `model.joblib`.
- Authored serving handler in `ml/serving/inference.py` (`model_fn`, `input_fn`, `predict_fn`, `output_fn`).
- Packaged model archive `ml/model.tar.gz` and authored `ml/deploy.py` using `SKLearnModel` and `ServerlessInferenceConfig` (2048 MB memory, max concurrency 2).
- Resolved container startup issue where `PYTHONPATH` needed to resolve `/opt/ml/model/code`, `/home/model-server/.local/lib/python3.10/site-packages`, and `/opt/ml/code`.

**Operations (2026-11-10):**
- Endpoint name: `cloudscale-category` deployed and verified `InService`.
- Tested endpoint invocation with `ml/test_endpoint.py`: returned categories and confidence scores successfully.
- Added `/api/suggest-category` to `app/app.py` and UI button in `app/templates/new.html`.

**Commit:** phase9: sagemaker training + serverless endpoint + in-app category suggestion

---

## Phase 10: Bedrock (Description Generator)

**Inception (2026-11-10):**
- Goal: Use AWS Bedrock foundation model (`amazon.nova-lite-v1:0`) via Bedrock Converse API to generate factual 2-3 sentence listing descriptions from user notes.
- Requirements: Restrict EC2 role to `bedrock:InvokeModel` on the foundation model, provide `/api/write-description` in Flask, and connect to "Write description" UI button.

**Construction (2026-11-10):**
- Verified access to `amazon.nova-lite-v1:0` in `us-east-1` using Bedrock Converse API.
- Updated `terraform/compute.tf` with `bedrock:InvokeModel` on `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0`.
- Added `BEDROCK_MODEL` and `brt` client to `app/app.py` and implemented `/api/write-description` route with prompt injection guardrails.
- Rebuilt `build/app.zip`, applied changes with Terraform, and started ASG rolling instance refresh on `cloudscale-asg`.

**Operations (2026-11-10):**
- Bedrock model ID: `amazon.nova-lite-v1:0`.
- Tested model response: successfully produces concise factual lost & found descriptions without hallucinating or leaking contact info.
- UI integration: User enters title, category, and optional notes; clicks "Write description"; description field auto-populates.

**Commit:** phase10: bedrock description generator - inception/construction/ops
