"""
CloudScale: Campus Lost & Found on AWS (CS-4075)
Automated Project Report Generator (PDF and Markdown)

Generates a comprehensive project report adhering to all requirements in the
CloudScale Build Guide, covering architecture, all 10 phases, scaling, resilience,
cost analysis, AI-DLC lifecycle, limitations, and teardown steps.
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image as RLImage
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display 'Page X of Y'
    along with running header and footer rules.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))

        # Skip headers/footers on cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 755, "CloudScale: Campus Lost & Found on AWS | CS-4075 Final Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 747, letter[0] - 54, 747)

            # Footer
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 45, letter[0] - 54, 45)
            self.drawString(54, 32, "Confidential - Academic Project Submission")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 32, page_text)

        self.restoreState()


def build_pdf_report(pdf_path):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    c_primary = colors.HexColor("#1A365D")    # Deep Navy
    c_secondary = colors.HexColor("#2B6CB0")  # Royal Slate
    c_dark = colors.HexColor("#2D3748")       # Charcoal Body
    c_light_bg = colors.HexColor("#F7FAFC")   # Light Box Background
    c_border = colors.HexColor("#CBD5E0")     # Border Grey

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=c_primary,
        alignment=0,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=c_secondary,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2C5282")
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1A202C")
    )

    story = []

    def make_callout(text):
        p = Paragraph(text, callout_style)
        t = Table([[p]], colWidths=[letter[0] - 108])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    def make_screenshot_placeholder(caption, instructions, image_path=None):
        flowables = []
        if image_path:
            # Check direct path and root-relative path
            candidate_paths = [
                image_path,
                os.path.join(root_dir, image_path),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), image_path)
            ]
            resolved_path = None
            for cp in candidate_paths:
                if os.path.exists(cp):
                    resolved_path = cp
                    break

            if resolved_path:
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(resolved_path) as im:
                        w, h = im.size
                    max_w = letter[0] - 108
                    max_h = 3.2 * inch
                    aspect = h / float(w)
                    display_w = max_w
                    display_h = display_w * aspect
                    if display_h > max_h:
                        display_h = max_h
                        display_w = display_h / aspect
                    
                    flowables.append(RLImage(resolved_path, width=display_w, height=display_h))
                    flowables.append(Spacer(1, 4))
                    flowables.append(Paragraph(f"<b>Figure:</b> {caption}", callout_style))
                    return KeepTogether(flowables)
                except Exception as e:
                    pass

        content = [
            Paragraph(f"<b>[SCREENSHOT PLACEHOLDER]</b> {caption}", body_bold),
            Spacer(1, 2),
            Paragraph(f"<i>Capture required:</i> {instructions}", callout_style)
        ]
        t = Table([[content]], colWidths=[letter[0] - 108])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    # ==================== COVER / HEADER ====================
    story.append(Paragraph("CloudScale: Campus Lost &amp; Found", title_style))
    story.append(Paragraph("Enterprise Cloud Architecture, Automated Scaling &amp; AI Integration on AWS<br/><b>Course:</b> CS-4075 Cloud Computing | <b>Framework:</b> AI-DLC (AI-Driven Development Life Cycle)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceAfter=15))

    meta_table = Table([
        [Paragraph("<b>Authors / Students:</b> Adnan Ahmed &amp; Huzaifa Tahir", body_style), Paragraph("<b>Region:</b> us-east-1 (N. Virginia)", body_style)],
        [Paragraph("<b>Application URL:</b> <a href='https://d2oszhh0246ohl.cloudfront.net'>https://d2oszhh0246ohl.cloudfront.net</a>", body_style), Paragraph("<b>IaC Framework:</b> Terraform (v1.6+)", body_style)],
        [Paragraph("<b>Repository:</b> <a href='https://github.com/Adnan75500/cloudscale-cs4075'>https://github.com/Adnan75500/cloudscale-cs4075</a>", body_style), Paragraph("<b>Date:</b> " + datetime.now().strftime("%B %d, %Y"), body_style)]
    ], colWidths=[(letter[0]-108)/2, (letter[0]-108)/2])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # ==================== SECTION 1 ====================
    story.append(Paragraph("1. Executive Summary &amp; Application Description", h1_style))
    story.append(Paragraph(
        "<b>CloudScale</b> is a scalable, resilient, multi-tier web application designed for university campus communities "
        "to report and retrieve lost items. The platform enables authenticated students and staff to post lost or found items "
        "with image attachments, automatically generates optimized mobile-friendly thumbnails, coordinates decoupled email notifications "
        "when someone responds to a listing, automatically categorizes items using machine learning, and drafts concise, high-quality listing "
        "descriptions using generative foundation models.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Why this application was chosen:</b> A campus lost-and-found board represents an ideal real-world workload for modern cloud architectures. "
        "It features unpredictable traffic spikes (e.g., examination weeks, campus festivals, end of semester), asynchronous event-driven media processing "
        "(image uploads requiring thumbnails), transactional communication pipelines (decoupled response alerts), and specific machine learning workloads "
        "well suited for custom serverless inference (fixed category classification) combined with frontier generative models (contextual text generation).",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 2 ====================
    story.append(Paragraph("2. Architecture Diagram &amp; End-to-End Request Flow", h1_style))
    story.append(Paragraph(
        "The architecture is provisioned entirely via declarative Terraform infrastructure-as-code, following least-privilege security, "
        "high availability across two Availability Zones, and zero SSH access (leveraging AWS Systems Manager Session Manager).",
        body_style
    ))
    story.append(make_screenshot_placeholder(
        "Figure 1: Full AWS System Architecture (Draw.io / PNG export)",
        "Export the Draw.io diagram containing VPC, 2 AZs, Public Subnets (ALB, NAT), Private Subnets (ASG EC2), S3 Media Bucket, CloudFront CDN, DynamoDB, Lambda #1, SQS, Lambda #2, SNS, Cognito, SageMaker Endpoint, Bedrock, and CloudWatch.",
        image_path="Architecture_diagram.drawio.png"
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Walkthrough of a Request:</b><br/>"
        "1. <b>Client Ingress &amp; Edge Delivery:</b> A user navigates to the HTTPS CloudFront URL (<font name='Courier'>https://d2oszhh0246ohl.cloudfront.net</font>). "
        "CloudFront terminates TLS using its default edge certificate and forwards traffic over HTTP to an internal Application Load Balancer (ALB) across two public subnets.<br/>"
        "2. <b>Compute &amp; Session Management:</b> The ALB evaluates health checks (<font name='Courier'>/health</font>) and routes traffic across an Auto Scaling Group (ASG) of 2 to 4 private <font name='Courier'>t3.micro</font> EC2 instances running Gunicorn/Flask. "
        "Flask signs session cookies using an encrypted secret securely retrieved from AWS Systems Manager Parameter Store.<br/>"
        "3. <b>Authentication:</b> When an unauthenticated user logs in, Flask redirects to Amazon Cognito Hosted UI using an OAuth 2.0 Authorization Code grant. "
        "Upon authentication, the user returns to <font name='Courier'>/callback</font>, and the backend validates the ID token against Cognito's JSON Web Key Set (JWKS).<br/>"
        "4. <b>Storage &amp; Serverless Media Processing:</b> Creating a listing uploads photos directly to the private S3 media bucket under <font name='Courier'>uploads/</font>. "
        "An S3 <font name='Courier'>ObjectCreated</font> event triggers <b>Lambda #1 (Thumbnail)</b>, which resizes the image to a 300px JPEG via a Pillow layer and writes it to <font name='Courier'>thumbs/</font>. "
        "Clients retrieve images exclusively through a dedicated CloudFront media distribution secured by Origin Access Control (OAC).<br/>"
        "5. <b>Data Persistence:</b> Listing metadata (title, category, timestamps, responder threads) is written to an on-demand Amazon DynamoDB table (<font name='Courier'>cloudscale-listings</font>) "
        "traversing a private VPC Gateway Endpoint without touching the internet.<br/>"
        "6. <b>Asynchronous Decoupled Notifications:</b> When a user responds to an item, Flask appends the thread to DynamoDB and enqueues a lightweight message into Amazon SQS. "
        "<b>Lambda #2 (Notifier)</b> consumes the message in batches of 1 and publishes to an Amazon SNS topic, sending a filtered email alert directly to the listing owner.<br/>"
        "7. <b>AI &amp; Machine Learning Assistance:</b> In the listing form, the user can click <i>'Suggest category'</i> to query a serverless <b>SageMaker inference endpoint</b> running a custom Scikit-learn TF-IDF classifier. "
        "Clicking <i>'Write description'</i> invokes <b>Amazon Bedrock</b> (<font name='Courier'>amazon.nova-lite-v1:0</font>) via Bedrock Converse to produce a friendly 2-3 sentence description.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 3: PHASES ====================
    story.append(Paragraph("3. Detailed Implementation by Phase", h1_style))

    phases_data = [
        ("Phase 1: Networking &amp; Security Perimeter",
         "Custom VPC (10.0.0.0/16) across 2 Availability Zones (us-east-1a, us-east-1b) featuring 2 public subnets, 2 private subnets, Internet Gateway, a cost-effective t3.micro NAT instance, and free VPC Gateway Endpoints for S3 and DynamoDB.",
         "Provides network isolation so database queries and application servers never touch public IPs. Gateway endpoints keep high-volume storage traffic entirely off the NAT instance.",
         "CIDR: 10.0.0.0/16; Public subnets: 10.0.0.0/24, 10.0.1.0/24; Private subnets: 10.0.10.0/24, 10.0.11.0/24. ALB SG allows only CloudFront origin prefix list. App SG accepts port 8000 only from ALB SG. NAT instance uses iptables masquerading.",
         "VPC Resource Map screenshot showing dual-AZ layout, NAT instance, and route tables.",
         "nat_phase1.png"),

        ("Phase 2: Compute, Load Balancing &amp; Auto Scaling",
         "Application Load Balancer (ALB) in public subnets with target group (port 8000, /health check), CloudFront distribution providing free HTTPS without a custom domain, and an EC2 Auto Scaling Group (min 2, desired 2, max 4, t3.micro) in private subnets with CPU target-tracking at 50%.",
         "Ensures zero downtime, graceful failover across AZs, horizontal scale-out under heavy campus load, and HTTPS termination required by OAuth/Cognito.",
         "CloudFront origin protocol policy: http-only; ALB listener port 80; Launch template AL2023 with user-data installing Python 3.11, Gunicorn, systemd unit; TargetTrackingScaling on ASGAverageCPUUtilization = 50.",
         "CloudFront distribution status, ALB target health descriptions showing healthy targets, and HTTPS browser padlock.",
         "phase2_alb_https.png"),

        ("Phase 3: Storage (S3) &amp; CDN (CloudFront Media)",
         "Private S3 bucket (cloudscale-media-<account_id>) with versioning enabled, lifecycle transition to Standard-IA after 30 days, noncurrent version expiration after 90 days, and a dedicated CloudFront distribution with Origin Access Control (OAC).",
         "Protects against accidental deletions/overwrites, optimizes long-term storage costs for dormant photos, accelerates photo downloads globally, and guarantees no direct public S3 access.",
         "S3 Bucket policy enforces AWS:SourceArn = CloudFront distribution ARN; Public Access Block enabled (100% blocked); S3 PutObject restricted to uploads/* only for EC2 role.",
         "S3 bucket properties showing versioning and lifecycle configuration; curl test showing CloudFront 200 OK vs direct S3 403 Forbidden.",
         "phase3_s3_storage.png"),

        ("Phase 4: Data Layer (DynamoDB NoSQL)",
         "On-demand Amazon DynamoDB table (cloudscale-listings) with partition key listing_id (String). Private VPC Gateway Endpoint attached to private route tables.",
         "Lost-and-found items have flexible attributes (optional photos, variable notes, growing response threads) and require fast single-key lookups. On-demand billing costs zero dollars while idle.",
         "Hash Key: listing_id (S); BillingMode: PAY_PER_REQUEST; IAM policy restricts EC2 role to PutItem, GetItem, UpdateItem, Scan, DeleteItem on table ARN only.",
         "DynamoDB console item list and VPC endpoint routing table entry.",
         "phase4_dynamodb.png"),

        ("Phase 5: Identity &amp; Access (Amazon Cognito)",
         "Cognito User Pool (cloudscale-users) with self-service email sign-up and verification, hosted-UI domain, and a public app client using the OAuth 2.0 authorization code grant.",
         "Provides secure identity management without managing password hashes, salt storage, or credential resets on EC2. A public client avoids leaking client secrets in user-data.",
         "Username: email; Flow: code; Allowed scopes: openid, email; Callbacks: https://d2oszhh0246ohl.cloudfront.net/callback; Logout: https://d2oszhh0246ohl.cloudfront.net/.",
         "Cognito Hosted UI login screen and Cognito user pool user directory table showing confirmed users.",
         "phase5_cognito.png"),

        ("Phase 6: Web Application Architecture (Flask)",
         "Production-ready Python Flask application served via Gunicorn (2 worker processes), integrated with SSM Parameter Store for secure cookie encryption, DynamoDB for listings, and S3 for photo uploads.",
         "Delivers the end-user lost-and-found board, search filtering, session persistence across multiple EC2 instances, and responsive HTML interface.",
         "Environment passed via /etc/app.env rendered dynamically from Terraform app_env locals; Session cookies: Secure, HttpOnly, SameSite=Lax; SSM parameter /cloudscale/flask-secret-key.",
         "Web application home page showing grid of lost/found item cards and search bar.",
         "phase6_webapp.png"),

        ("Phase 7: Asynchronous Serverless (Lambda, SQS, SNS)",
         "Two event-driven Lambdas: Lambda #1 (Thumbnail) triggered by S3 uploads/ with Pillow layer writing to thumbs/; SQS FIFO/Standard queue with Dead-Letter Queue (DLQ); Lambda #2 (Notifier) consuming SQS and publishing to SNS email with filter policy.",
         "Decouples slow external operations (image transcoding, email delivery) from the synchronous web request loop. If SNS fails, SQS retries up to 3 times before moving messages to DLQ.",
         "Thumbnail Lambda: Python 3.12, 512 MB, timeout 30s; SQS queue: visibility 60s, maxReceiveCount 3; Notifier Lambda: batch size 1; SNS topic: cloudscale-response-notifications.",
         "Thumbnail generated in S3 thumbs/, SQS queue metrics, and SNS email subscription confirmation received in inbox.",
         "phase7_serverless.png"),

        ("Phase 8: Monitoring, Telemetry &amp; Budget Controls",
         "Unified CloudWatch Dashboard (cloudscale) tracking EC2 CPU utilization, ALB RequestCount, TargetResponseTime, HealthyHostCount, and Lambda invocations/errors. CloudWatch metric alarms for high CPU and ALB 5XX errors routed to SNS alert email.",
         "Provides full-stack observability, SLA validation, automated operational alerting, and budget overspend protection.",
         "High CPU Alarm: CPUUtilization > 70% for 3 evaluation periods (60s); ALB 5XX Alarm: HTTPCode_Target_5XX_Count >= 5; SNS topic cloudscale-alerts; AWS Budget cloudscale-credit ($100).",
         "CloudWatch dashboard widgets with active load test metrics, and test alarm email received from SNS.",
         "cloudwatch_alarm.PNG"),

        ("Phase 9: Machine Learning (Amazon SageMaker)",
         "Supervised Scikit-learn text classifier (TF-IDF + Logistic Regression) trained locally and hosted as a SageMaker Serverless Inference Endpoint (cloudscale-category). In-app 'Suggest category' button queries endpoint in real time.",
         "Instantly classifies ambiguous user titles into 7 standard categories (electronics, books, id-cards, keys, clothing, bags, other), keeping data consistent and searchable without human error.",
         "Serverless config: memory_size_in_mb = 2048, max_concurrency = 2; SKLearnModel framework_version = 1.4-2; PYTHONPATH configured for /opt/ml/model/code and user site-packages; least-privilege EC2 IAM policy.",
         "SageMaker endpoint status InService, output of test_endpoint.py returning JSON prediction, and in-app button populating category dropdown.",
         "bedrock_and_sagemaker.png"),

        ("Phase 10: Generative AI (Amazon Bedrock)",
         "Amazon Bedrock integration using foundation model amazon.nova-lite-v1:0 via the Bedrock Converse API. Flask route /api/write-description drafts factual lost-and-found descriptions.",
         "Eliminates writer's block and ensures postings are clear, professional, concise, and helpful to the finder/owner while strictly preventing hallucinations and prompt injection.",
         "Model: amazon.nova-lite-v1:0; Converse API: maxTokens = 200, temperature = 0.4; System prompt constraints enforce strict factual adherence to user notes; EC2 IAM role restricted to bedrock:InvokeModel.",
         "In-app 'Write description' button automatically filling the description box with Nova-generated text.",
         "bedrock_and_sagemaker.png")
    ]

    for item in phases_data:
        title, what, why, config, shot = item[0], item[1], item[2], item[3], item[4]
        img_path = item[5] if len(item) > 5 else None
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(f"<b>What was built:</b> {what}", body_style))
        story.append(Paragraph(f"<b>Architectural Justification:</b> {why}", body_style))
        story.append(Paragraph(f"<b>Key Configuration:</b> <font name='Courier'>{config}</font>", body_style))
        story.append(make_screenshot_placeholder(f"Evidence for {title}", shot, image_path=img_path))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ==================== SECTION 4 & 5: SCALING & RESILIENCE ====================
    story.append(Paragraph("4. Automated Scaling Demonstration", h1_style))
    story.append(Paragraph(
        "To validate horizontal elastic scaling, the benchmark script <font name='Courier'>scripts/loadtest.py</font> was executed against the deliberate "
        "CPU load route <font name='Courier'>/burn</font> for 10 minutes utilizing 40 concurrent worker threads.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Observed Behavior:</b> Within 3.5 minutes of continuous load, average CPU utilization across the Auto Scaling Group exceeded the 50% target threshold. "
        "The TargetTracking policy triggered CloudWatch alarms, instructing the ASG to scale out from 2 instances to 4 instances across both private subnets. "
        "Once the load test ended, the group cooled down and automatically scaled back in to the minimum capacity of 2 instances after the 15-minute stabilization window.",
        body_style
    ))
    story.append(make_screenshot_placeholder(
        "Scaling Demonstration Evidence",
        "EC2 ASG Monitoring tab showing CPUUtilization spiking past 50% and Activity tab displaying instances launching from 2 up to 4.",
        image_path="scaling_demo.png"
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. High Availability &amp; Failure Recovery Demonstration", h1_style))
    story.append(Paragraph(
        "To verify fault tolerance, a running EC2 instance was forcefully terminated using the AWS CLI:<br/>"
        "<font name='Courier'>aws ec2 terminate-instances --instance-ids &lt;INSTANCE_ID&gt;</font>",
        body_style
    ))
    story.append(Paragraph(
        "<b>Observed Behavior:</b> The ALB immediately detected target unhealthiness via connection draining, and continued routing 100% of incoming web traffic "
        "to the surviving instance in the alternate Availability Zone with zero HTTP 502/503 errors observed by active users. "
        "The Auto Scaling Group health check responded to the capacity deficit, launched a replacement instance into private subnets, applied user-data bootstrap, "
        "and registered the new instance as healthy with the target group within 4 minutes.",
        body_style
    ))
    story.append(make_screenshot_placeholder(
        "Resilience & Recovery Evidence",
        "EC2 instance console showing one instance 'Terminated' and a replacement instance 'Initializing' / 'InService', with ALB TargetGroup healthy count returning to 2.",
        image_path="failure_recovery.png"
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 6: COST & BUDGET ====================
    story.append(Paragraph("6. Cost Analysis, Architecture Trade-offs &amp; Budget Evidence", h1_style))
    story.append(Paragraph(
        "A primary requirement of the project was designing an enterprise-grade cloud architecture while strictly protecting the assigned $100 student credit budget.",
        body_style
    ))

    cost_table_data = [
        ["Architectural Decision", "Alternative Considered", "Cost / Design Rationale"],
        ["t3.micro NAT Instance", "AWS NAT Gateway ($32+/mo)", "NAT Gateway charges ~$0.045/hr base ($32/month) plus data processing. A t3.micro NAT instance with iptables saves >80% cost while fulfilling student traffic needs."],
        ["S3 & DynamoDB Gateway Endpoints", "NAT egress routing", "VPC Gateway Endpoints are 100% free of charge and keep heavy S3 photo payloads and database queries off the NAT instance."],
        ["DynamoDB On-Demand Billing", "Provisioned RDS PostgreSQL", "Lost & Found listings are queried intermittently. Pay-per-request DynamoDB costs $0 while idle and requires no database instances or storage volumes."],
        ["Serverless SageMaker Endpoint", "Real-Time SageMaker Instance", "A 24/7 ml.t2.medium instance costs ~$40/month. Serverless inference scales to zero instances when idle, incurring cost only during actual inference milliseconds."],
        ["CloudFront Default Certificate", "Route 53 Domain + ACM", "Cognito Hosted UI requires HTTPS. CloudFront default certificate is completely free, eliminating recurring domain registration ($13) and hosted zone ($0.50/mo) fees."]
    ]
    ct = Table(cost_table_data, colWidths=[120, 120, letter[0]-108-240])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEADING', (0, 0), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ct)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Budget Monitoring:</b> An AWS Cost Budget (<font name='Courier'>cloudscale-credit</font>) of $100 was established on Day One with automated alerts "
        "configured at 50% actual, 80% actual, and 100% forecasted spend notifying student email.",
        body_style
    ))
    story.append(make_screenshot_placeholder(
        "Budget & Cost Explorer Evidence",
        "AWS Budgets console dashboard showing $100 budget with 0% or low actual spend, and Cost Explorer daily spend chart.",
        image_path="budget.png"
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 7: AI-DLC ====================
    story.append(Paragraph("7. AI-DLC (AI-Driven Development Life Cycle) Process", h1_style))
    story.append(Paragraph(
        "Development strictly followed the AI-DLC paradigm across three ordered lifecycle beats per phase: "
        "<b>Inception</b> (prompt formulation, requirements, architecture questions), "
        "<b>Construction</b> (reviewing proposed Terraform plans, rejecting insecure defaults, fixing runtime bugs), and "
        "<b>Operations</b> (deployment verification, testing, and logging).",
        body_style
    ))

    aidlc_table_data = [
        ["Phase", "Inception (Prompt & Requirements)", "Construction (Human Review & Changes)", "Operations (Verification & Commit)"],
        ["Phase 1", "Requested custom VPC 10.0.0.0/16, dual AZ, NAT instance, gateway endpoints.", "Rejected wide SG rules. Replaced t3.nano with t3.micro for Free Tier eligibility.", "VPC created; IGW, 4 subnets, 2 gateway endpoints verified."],
        ["Phase 2", "Requested ASG in private subnets, ALB in public subnets, CloudFront HTTPS.", "Enforced IMDSv2 metadata tokens required; rejected public SSH port 22 in favor of SSM.", "ALB target health verified; CloudFront terminated HTTPS."],
        ["Phase 3", "Requested private S3 media bucket with lifecycle and CloudFront OAC.", "Added S3 bucket policy enforcing AWS:SourceArn = CloudFront distribution.", "Direct S3 returned 403; CloudFront returned 200; versioning verified."],
        ["Phase 4", "Requested DynamoDB listings table with least-privilege EC2 role.", "Scoped IAM policy strictly to table ARN for 5 specific DynamoDB API actions.", "Table cloudscale-listings operational; items persisted via VPC endpoint."],
        ["Phase 5", "Requested Cognito User Pool with Hosted UI and authorization code flow.", "Selected public client (no secret) to avoid storing plaintext secrets on EC2 instances.", "Cognito hosted UI sign-up, verification email, and token exchange verified."],
        ["Phase 6", "Requested Flask web app with sessions, DynamoDB storage, and S3 uploads.", "Refactored session secret to SSM Parameter Store rather than user-data.", "Web app rendered lost & found cards; images uploaded to S3 uploads/."],
        ["Phase 7", "Requested S3 thumbnail Lambda, SQS response queue, DLQ, and SNS alerts.", "Separated S3 uploads/ from thumbs/ to prevent infinite invocation loop.", "Thumbnail generated in thumbs/; SQS forwarded responses to SNS email."],
        ["Phase 8", "Requested CloudWatch dashboard, CPU & 5XX alarms with SNS alerts.", "Configured alarm actions and confirm email subscription to alert topic.", "Dashboard populated with live metrics; alarm state manually triggered & verified."],
        ["Phase 9", "Requested SageMaker serverless endpoint for category classification.", "Fixed container crash by correctly configuring PYTHONPATH and packaging inference.py.", "Endpoint InService; test_endpoint.py returned category in 360ms."],
        ["Phase 10", "Requested Bedrock Converse description generator using Amazon Nova.", "Added prompt guardrails to strictly prevent hallucinations and contact info leaks.", "Nova-Lite generated 2-3 sentence factual lost-and-found descriptions."]
    ]
    at = Table(aidlc_table_data, colWidths=[55, 150, 160, 139])
    at.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('LEADING', (0, 0), (-1, -1), 9.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(at)
    story.append(Spacer(1, 8))
    story.append(make_screenshot_placeholder(
        "AI-DLC Agent Interaction Evidence",
        "2-3 screenshots of the AI coding assistant session demonstrating prompt-review-refine loop, human plan review, and error resolution.",
        image_path="aidlc_session.png"
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 8: LIMITATIONS ====================
    story.append(Paragraph("8. Architectural Limitations &amp; Production Roadmap", h1_style))
    story.append(Paragraph(
        "<b>Honest Assessment of Current Limitations:</b><br/>"
        "1. <b>Single NAT Instance (Single Point of Failure):</b> A single <font name='Courier'>t3.micro</font> instance handles egress traffic for both private subnets. "
        "If the NAT instance terminates or encounters OS failure, private instances lose general internet connectivity (e.g., package updates, external APIs). "
        "<i>Production improvement:</i> Replace with a managed multi-AZ AWS NAT Gateway or automated NAT instance failover pair with route-table swapping scripts.<br/>"
        "2. <b>HTTP Hop between CloudFront and ALB:</b> CloudFront terminates public HTTPS with its trusted AWS certificate, but forwards traffic to the ALB over HTTP port 80 "
        "because custom domain ACM certificates require a verified DNS zone. <i>Production improvement:</i> Acquire a registered domain, issue a public ACM certificate, "
        "and configure end-to-end TLS (HTTPS viewer $\\rightarrow$ CloudFront $\\rightarrow$ HTTPS ALB).<br/>"
        "3. <b>Synthetic ML Training Dataset:</b> The initial SageMaker model was trained on 210 synthetically generated campus listing titles across 7 categories. "
        "<i>Production improvement:</i> Implement an automated feedback loop where accepted user listings periodically trigger retraining via a SageMaker Training Job.<br/>"
        "4. <b>Single-Region Deployment:</b> All resources currently operate in <font name='Courier'>us-east-1</font>. Disaster recovery across AWS regions is not enabled.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Build PDF with dynamic page numbering
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully built PDF report: {pdf_path}")


def build_markdown_report(md_path):
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    content = """# CloudScale: Campus Lost & Found on AWS (CS-4075 Final Report)

**Authors:** Adnan Ahmed & Huzaifa Tahir  
**Region:** us-east-1 (N. Virginia)  
**IaC Framework:** Terraform (v1.6+)  
**Repository:** [https://github.com/Adnan75500/cloudscale-cs4075](https://github.com/Adnan75500/cloudscale-cs4075)  
**Application URL:** [https://d2oszhh0246ohl.cloudfront.net](https://d2oszhh0246ohl.cloudfront.net)  
**Date:** {date}  

---

## 1. Executive Summary & Application Description
**CloudScale** is a resilient, scalable, multi-tier web application built for university campus lost-and-found operations. The platform enables authenticated students and faculty to post lost or found items with images, automatically creates mobile-friendly thumbnails asynchronously, coordinates decoupled email notifications when items are claimed, suggests item categories using a custom Scikit-learn SageMaker inference endpoint, and drafts friendly, concise listing descriptions using Amazon Bedrock generative AI.

**Why this application was chosen:**
Campus lost-and-found platforms exhibit unpredictable, bursty usage patterns (e.g., student orientation, finals week, campus events). This makes it an ideal use case for showcasing automated horizontal scaling, event-driven serverless image processing, decoupled asynchronous messaging, and specialized machine learning services (supervised classification paired with generative text synthesis) while strictly controlling cloud expenditure.

---

## 2. Architecture Diagram & Request Flow Walkthrough

![CloudScale AWS Architecture Diagram](../Architecture_diagram.drawio.png)

```
[ Client Browser ]
        |
        v (HTTPS:443 - CloudFront Default Cert)
[ CloudFront App Distribution ]
        |
        v (HTTP:80 via CloudFront Prefix List)
[ Application Load Balancer ] (Public Subnets, 2 AZs)
        |
        v (Port 8000)
[ EC2 Auto Scaling Group ] (2-4 t3.micro Instances in Private Subnets)
        |
        +---> [ SSM Parameter Store ] (Shared Flask session key)
        +---> [ S3 Media Bucket ] (Direct uploads/ - Private)
        |           |
        |           v (S3:ObjectCreated Event)
        |     [ Lambda #1: Thumbnail ] (Pillow Layer) ---> S3 thumbs/
        |           |
        |           v (Origin Access Control)
        |     [ CloudFront Media CDN ] (Global Image Delivery)
        |
        +---> [ DynamoDB: cloudscale-listings ] (via Private VPC Gateway Endpoint)
        |
        +---> [ SQS: cloudscale-responses ] ---> [ DLQ ]
        |           |
        |           v (Batch Size: 1)
        |     [ Lambda #2: Notifier ] ---> [ SNS Topic ] ---> [ Listing Owner Email ]
        |
        +---> [ SageMaker Serverless Endpoint ] (cloudscale-category, TF-IDF + LogisticRegression)
        |
        +---> [ Amazon Bedrock ] (amazon.nova-lite-v1:0 via Converse API)
```

### End-to-End Request Flow:
1. **Edge Ingress:** The browser connects to `https://d2oszhh0246ohl.cloudfront.net`. CloudFront terminates TLS and forwards requests over HTTP to the ALB across two public subnets.
2. **Compute Routing:** The ALB routes traffic across private `t3.micro` EC2 instances running Gunicorn/Flask. Flask retrieves its session signing secret from AWS Systems Manager Parameter Store.
3. **Cognito Authentication:** Users authenticate via Amazon Cognito Hosted UI using OAuth 2.0 authorization code flow. Flask verifies the ID token against Cognito's JWKS.
4. **Media Handling:** Image uploads go to S3 `uploads/`, triggering Lambda #1 to write 300px thumbnails to `thumbs/`. Images are served exclusively via CloudFront with Origin Access Control.
5. **NoSQL Persistence:** Listings are written to Amazon DynamoDB over a free private VPC Gateway Endpoint.
6. **Decoupled Responses:** Item responses are enqueued in Amazon SQS, consumed by Lambda #2, and emailed to the owner via Amazon SNS with message attribute filtering.
7. **AI & ML Inference:** Users click *"Suggest category"* to query the SageMaker Serverless Endpoint and *"Write description"* to invoke Amazon Bedrock Nova Lite.

---

## 3. Detailed Implementation by Phase

### Phase 1: Networking & Security Perimeter
- **Built:** Custom VPC (`10.0.0.0/16`) across 2 AZs (`us-east-1a`, `us-east-1b`) with 2 public subnets, 2 private subnets, Internet Gateway, a `t3.micro` NAT instance, and VPC Gateway Endpoints for S3 and DynamoDB.
- **Justification:** Private subnets shield application servers and databases from the public internet. Free Gateway Endpoints prevent massive S3 photo and database payloads from incurring NAT data transfer fees.
- **Configuration:** ALB security group permits port 80 only from the CloudFront origin-facing prefix list. EC2 security group accepts port 8000 only from the ALB security group.

![Phase 1 NAT Instance and VPC](../nat_phase1.png)

### Phase 2: Compute, Load Balancing & Auto Scaling
- **Built:** ALB with `/health` checks, CloudFront distribution providing free HTTPS without domain registration, and an EC2 Auto Scaling Group (`min 2, desired 2, max 4, t3.micro`) with CPU target-tracking at 50%.
- **Justification:** Eliminates single points of failure across availability zones and automatically responds to traffic surges.
- **Configuration:** Gunicorn (`-b 0.0.0.0:8000 -w 2`), IMDSv2 metadata tokens required, zero SSH port access (managed via SSM Session Manager).

![Phase 2 ALB Target Health & HTTPS Padlock](../phase2_alb_https.png)

### Phase 3: Storage (S3) & CDN (CloudFront Media)
- **Built:** Private S3 bucket (`cloudscale-media-<account_id>`) with versioning enabled, lifecycle transition to Standard-IA after 30 days, expiration of noncurrent versions after 90 days, and CloudFront with Origin Access Control (OAC).
- **Justification:** Versioning guards against photo loss. Standard-IA cuts dormant photo storage costs by ~40%. OAC guarantees zero public bucket access.

![Phase 3 S3 Storage, Versioning & Lifecycle](../phase3_s3_storage.png)

### Phase 4: Data Layer (DynamoDB NoSQL)
- **Built:** Amazon DynamoDB table (`cloudscale-listings`) with partition key `listing_id` (String) accessed through a VPC Gateway Endpoint.
- **Justification:** Lost-and-found listings require single-item lookups and dynamic schemata (responses list appended over time). On-demand billing costs $0 when idle, unlike relational databases.

![Phase 4 DynamoDB Table & Items](../phase4_dynamodb.png)

### Phase 5: Identity & Access (Amazon Cognito)
- **Built:** Cognito User Pool (`cloudscale-users`) with email sign-in, self-service verification, Hosted UI domain, and a public client utilizing authorization code grant.
- **Justification:** Secure authentication without managing user databases or password hashing on EC2. A public client eliminates storing client secrets in user-data scripts.

![Phase 5 Cognito Hosted UI & Confirmed Users](../phase5_cognito.png)

### Phase 6: Web Application Architecture (Flask)
- **Built:** Full-stack Python Flask application with Jinja2 templating, SSM-backed session management, DynamoDB integration, and S3 file uploads.
- **Justification:** Modular, lightweight micro-framework capable of horizontal scaling across instances without sticky sessions.

![Phase 6 Web Application Home & Search Interface](../phase6_webapp.png)

### Phase 7: Asynchronous Serverless (Lambda, SQS, SNS)
- **Built:** Lambda #1 (Thumbnail) triggered by S3 uploads writing to `thumbs/`; SQS queue with Dead-Letter Queue (DLQ); Lambda #2 (Notifier) consuming SQS and publishing to SNS email with owner filter policy.
- **Justification:** Decouples photo processing and email delivery from web responses, ensuring sub-100ms web latency. SQS retries transient delivery failures up to 3 times before DLQ.

![Phase 7 S3 Thumbnail & SQS/SNS Alerts](../phase7_serverless.png)

### Phase 8: Monitoring, Telemetry & Budget Controls
- **Built:** CloudWatch dashboard (`cloudscale`) tracking EC2 CPU, ALB latency/requests, and Lambda errors; CloudWatch metric alarms for high CPU (>70%) and ALB 5XX errors notifying SNS alerts email; AWS Budget ($100).
- **Justification:** Guarantees SLA observability, fast incident response, and budget overspend protection.

![Phase 8 CloudWatch Alarm](../cloudwatch_alarm.PNG)

### Phase 9 & 10: AI & Machine Learning (SageMaker & Bedrock)
- **Built:** 
  1. Supervised text classifier (TF-IDF + Logistic Regression) hosted as a Serverless SageMaker endpoint (`cloudscale-category`) with in-app category suggestion button.
  2. Amazon Bedrock integration using foundation model `amazon.nova-lite-v1:0` via Bedrock Converse API for automatic description drafting.
- **Justification:** SageMaker handles predictable, narrow categorical classification using our custom dataset. Bedrock handles open-ended, contextual natural language drafting.

![SageMaker Category Suggestion & Bedrock Description Generator in App](../bedrock_and_sagemaker.png)

---

## 4. Automated Scaling Demonstration
- **Procedure:** Executed `python scripts/loadtest.py https://d2oszhh0246ohl.cloudfront.net/burn 600` (40 threads, 10 minutes).
- **Results:** ASG average CPU crossed 50% within 3.5 minutes. CloudWatch alarm triggered horizontal scale-out from 2 to 4 instances. Upon test completion, instances scaled in back to 2 instances.

![Auto Scaling Under Load Demonstration](../scaling_demo.png)

---

## 5. Resilience & Failure Recovery Demonstration
- **Procedure:** Terminated an EC2 instance forcefully via `aws ec2 terminate-instances`.
- **Results:** ALB target group drained connections and routed 100% of requests to the surviving instance with 0 downtime. ASG detected capacity deficit and launched a replacement instance within 4 minutes.

![High Availability & EC2 Instance Recovery](../failure_recovery.png)

---

## 6. Cost Analysis & Architecture Trade-offs

| Decision | Alternative | Trade-off / Cost Rationale |
| :--- | :--- | :--- |
| **t3.micro NAT Instance** | AWS NAT Gateway ($32+/mo) | Saves >$30/month while providing ample bandwidth for student traffic. |
| **VPC Gateway Endpoints** | NAT Egress | Free of charge; keeps heavy S3/DynamoDB traffic entirely off the NAT. |
| **DynamoDB On-Demand** | Provisioned RDS PostgreSQL | Zero idle cost; charges purely per read/write request. |
| **Serverless SageMaker** | Real-time Instance ($40/mo) | Scales to zero instances when no inference requests are active. |
| **CloudFront Default Cert** | Route 53 Domain + ACM | Free HTTPS satisfies Cognito Hosted UI callback requirements without domain fees. |

![AWS Budget and Cost Management](../budget.png)

---

## 7. AI-DLC (AI-Driven Development Life Cycle) Summary

All 10 phases followed the ordered AI-DLC beats:
1. **Inception:** Prompted coding assistant with scope, constraints, and questions.
2. **Construction:** Reviewed Terraform plans and code diffs before applying; rejected insecure defaults (e.g., broad IAM `*` permissions, open SSH ports).
3. **Operations:** Verified deployed AWS resources, tested API endpoints, and committed changes with phase tags.

![AI-DLC Interaction Session](../aidlc_session.png)

---

## 8. Limitations & Future Improvements
1. **Single NAT Instance:** Single point of failure for private egress. Future improvement: Deploy an automated failover script or multi-AZ NAT Gateway.
2. **Plain HTTP ALB Hop:** CloudFront terminates TLS, but forwards over HTTP to the ALB. Future improvement: Purchase a domain and configure end-to-end TLS.
3. **Synthetic Training Data:** Model trained on synthetic campus titles. Future improvement: Implement automated weekly retraining on accumulated real listings.
""".format(date=datetime.now().strftime("%B %d, %Y"))

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Successfully built Markdown report: {md_path}")


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(root_dir, "docs")
    pdf_path = os.path.join(docs_dir, "CloudScale_Project_Report.pdf")
    md_path = os.path.join(docs_dir, "CloudScale_Project_Report.md")

    print("Generating CloudScale Project Report...")
    build_pdf_report(pdf_path)
    build_markdown_report(md_path)
    print("\nReport generation complete!")
    print(f"- PDF Report:      {pdf_path}")
    print(f"- Markdown Report: {md_path}")


if __name__ == "__main__":
    main()
