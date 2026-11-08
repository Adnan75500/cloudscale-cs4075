
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