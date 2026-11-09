
#!/bin/bash
set -e

dnf install -y python3.11 python3.11-pip unzip

cd /opt
aws s3 cp s3://${code_bucket}/app.zip app.zip --region ${region}

unzip -o app.zip -d /opt
cd /opt/app

python3.11 -m venv venv
./venv/bin/pip install -r requirements.txt

cat > /etc/app.env <<EOF
%{ for k, v in env ~}
${k}=${v}
%{ endfor ~}
EOF

cat > /etc/systemd/system/app.service <<EOF
[Unit]
Description=CloudScale app
After=network.target

[Service]
WorkingDirectory=/opt/app
EnvironmentFile=/etc/app.env
ExecStart=/opt/app/venv/bin/gunicorn -b 0.0.0.0:8000 -w 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now app
