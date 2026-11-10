import os
import zipfile

ZIP_NAME = "i230715_i230731_project.zip"

INCLUDE_DIRS = [
    "app",
    "terraform",
    "lambda",
    "ml",
    "scripts",
    "docs",
]

INCLUDE_FILES = [
    "SUBMISSION_LINKS.txt",
    "README.md",
    "AI-DLC-LOG.md",
    "AGENTS.md",
    ".gitignore",
    "Architecture_diagram.drawio.png",
    "demo_video.mp4",
    "teardown.png",
    "aceess-key_step_1.png",
    "aidlc_session.png",
    "bedrock_and_sagemaker.png",
    "budget.png",
    "cloudwatch_alarm.PNG",
    "failure_recovery.png",
    "nat_phase1.png",
    "phase2_alb_https.png",
    "phase3_s3_storage.png",
    "phase4_dynamodb.png",
    "phase5_cognito.png",
    "phase6_webapp.png",
    "phase7_serverless.png",
    "scaling_demo.png",
    "test.jpg"
]

EXCLUDE_DIR_NAMES = {
    ".terraform",
    "__pycache__",
    ".venv",
    ".kiro",
    ".git",
    "build"
}

def should_exclude(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    for p in parts:
        if p in EXCLUDE_DIR_NAMES:
            return True
    
    fname = os.path.basename(rel_path)
    if fname == ZIP_NAME:
        return True
    if fname.endswith(".tfstate") or fname.endswith(".tfstate.backup"):
        return True
    if fname.endswith(".tfplan"):
        return True
    if fname.endswith(".bin"):
        return True
    if fname.endswith("-log.txt") or fname == "boot-log.txt":
        return True
    if fname.endswith(".pyc"):
        return True
    return False

def make_archive():
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)
        print(f"Removed existing {ZIP_NAME}")

    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        # Add root files
        for fname in INCLUDE_FILES:
            if os.path.exists(fname):
                zipf.write(fname, arcname=fname)
                print(f"Added root file: {fname} ({os.path.getsize(fname):,} bytes)")
            else:
                print(f"WARNING: File not found: {fname}")

        # Add directories
        for dname in INCLUDE_DIRS:
            if not os.path.exists(dname):
                print(f"WARNING: Dir not found: {dname}")
                continue
            for root, dirs, files in os.walk(dname):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, start=".")
                    if should_exclude(rel_path):
                        continue
                    zipf.write(full_path, arcname=rel_path)
                    print(f"Added: {rel_path}")

    file_size_mb = os.path.getsize(ZIP_NAME) / (1024 * 1024)
    print(f"\n========================================================")
    print(f"Successfully generated {ZIP_NAME} ({file_size_mb:.2f} MB)")
    print(f"========================================================")

if __name__ == "__main__":
    make_archive()
