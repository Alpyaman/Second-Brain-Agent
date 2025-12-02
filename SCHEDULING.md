# Curator Agent Scheduling Guide

This guide shows you how to schedule the Curator Agent to run automatically using various scheduling tools.

## Quick Start

The `schedule_curator.py` script is designed for automated scheduling:

```bash
# Test the scheduler
python schedule_curator.py --discover-only

# Run full workflow
python schedule_curator.py

# Force update all repositories
python schedule_curator.py --force-update
```

## Phase 3: Maintenance Features

The scheduled runs include automatic maintenance:

✅ **Duplicate Detection**: Skips repositories already in collections
✅ **Update Detection**: Checks commit hashes to detect updates
✅ **Smart Re-Ingestion**: Only re-ingests if repository has changed
✅ **Force Update Option**: Force re-ingestion with `--force-update`

## Cron Jobs (Linux/macOS)

### Basic Cron Setup

1. **Open crontab editor**:
   ```bash
   crontab -e
   ```

2. **Add a cron job** (choose one):

   ```bash
   # Daily at 2 AM (recommended)
   0 2 * * * cd /path/to/Second-Brain-Agent && /path/to/venv/bin/python schedule_curator.py >> logs/curator.log 2>&1

   # Weekly on Sundays at 3 AM
   0 3 * * 0 cd /path/to/Second-Brain-Agent && /path/to/venv/bin/python schedule_curator.py >> logs/curator.log 2>&1

   # Daily at midnight, discovery only
   0 0 * * * cd /path/to/Second-Brain-Agent && /path/to/venv/bin/python schedule_curator.py --discover-only >> logs/discovery.log 2>&1

   # Every 6 hours (00:00, 06:00, 12:00, 18:00)
   0 */6 * * * cd /path/to/Second-Brain-Agent && /path/to/venv/bin/python schedule_curator.py >> logs/curator.log 2>&1
   ```

3. **Save and exit**. Cron will automatically start running the job.

### Cron Syntax Reference

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

**Common patterns**:
- `0 2 * * *` - Daily at 2 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sundays at midnight
- `0 3 1 * *` - Monthly on the 1st at 3 AM

### Advanced Cron Configuration

```bash
# Set environment variables in crontab
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
GOOGLE_API_KEY=your_key_here

# Multiple domains
0 2 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py --domains frontend >> logs/frontend.log 2>&1
0 3 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py --domains backend >> logs/backend.log 2>&1

# Save results to JSON
0 2 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py --output results/$(date +\%Y\%m\%d).json >> logs/curator.log 2>&1
```

## Systemd Timers (Linux)

For more advanced scheduling with better logging and management:

### 1. Create Service File

`/etc/systemd/system/curator-agent.service`:

```ini
[Unit]
Description=Curator Agent - Automated Repository Discovery
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/Second-Brain-Agent
Environment="PATH=/path/to/venv/bin:/usr/bin"
Environment="GOOGLE_API_KEY=your_key_here"
ExecStart=/path/to/venv/bin/python schedule_curator.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Create Timer File

`/etc/systemd/system/curator-agent.timer`:

```ini
[Unit]
Description=Run Curator Agent Daily
Requires=curator-agent.service

[Timer]
# Run daily at 2 AM
OnCalendar=daily
OnCalendar=02:00

# Run 10 minutes after boot if missed
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Enable and Start Timer

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timer (start on boot)
sudo systemctl enable curator-agent.timer

# Start timer now
sudo systemctl start curator-agent.timer

# Check timer status
sudo systemctl status curator-agent.timer

# View logs
journalctl -u curator-agent.service -f
```

### Timer Schedule Examples

```ini
# Daily at 2 AM
OnCalendar=daily
OnCalendar=02:00

# Weekly on Sundays at 3 AM
OnCalendar=Sun 03:00

# Every 6 hours
OnCalendar=*-*-* 00,06,12,18:00:00

# Monthly on the 1st at midnight
OnCalendar=monthly
OnCalendar=01 00:00
```

## Windows Task Scheduler

### Using PowerShell

1. **Open PowerShell as Administrator**

2. **Create scheduled task**:

```powershell
# Daily at 2 AM
$action = New-ScheduledTaskAction -Execute "python" -Argument "schedule_curator.py" -WorkingDirectory "C:\path\to\Second-Brain-Agent"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "CuratorAgent" -Action $action -Trigger $trigger -Settings $settings -Description "Automated repository discovery and ingestion"

# Weekly on Sundays at 3 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
Register-ScheduledTask -TaskName "CuratorAgent-Weekly" -Action $action -Trigger $trigger -Settings $settings
```

### Using GUI

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Basic Task**
3. Name: "Curator Agent"
4. Trigger: Daily, Weekly, or Monthly
5. Action: Start a program
   - Program: `python` or `pythonw` (for no console)
   - Arguments: `schedule_curator.py`
   - Start in: `C:\path\to\Second-Brain-Agent`
6. Finish and test

## Cloud Schedulers

### AWS EventBridge + Lambda

```python
# lambda_function.py
import subprocess
import os

def lambda_handler(event, context):
    """Run curator agent in Lambda"""
    os.chdir('/tmp')
    # Clone repo, install deps, run scheduler
    subprocess.run(['python', 'schedule_curator.py'])
    return {'statusCode': 200}
```

**EventBridge Rule**: `cron(0 2 * * ? *)` (Daily at 2 AM UTC)

### Google Cloud Scheduler + Cloud Functions

```yaml
# cloudfunctions-config.yaml
runtime: python39
entry_point: run_curator
```

```python
# main.py
def run_curator(request):
    """HTTP Cloud Function to run curator"""
    import subprocess
    result = subprocess.run(['python', 'schedule_curator.py'], capture_output=True)
    return result.stdout
```

**Scheduler**: `0 2 * * *` (Daily at 2 AM)

### Azure Logic Apps

Create a Logic App with:
1. **Trigger**: Recurrence (Daily, Weekly, etc.)
2. **Action**: HTTP Request to your curator endpoint or Azure Function

## Docker + Cron

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Add cron job
RUN apt-get update && apt-get install -y cron
COPY cron-curator /etc/cron.d/curator
RUN chmod 0644 /etc/cron.d/curator
RUN crontab /etc/cron.d/curator

CMD ["cron", "-f"]
```

`cron-curator`:

```
0 2 * * * cd /app && python schedule_curator.py >> /var/log/curator.log 2>&1
```

## Monitoring and Logging

### Log Rotation

Create `/etc/logrotate.d/curator-agent`:

```
/path/to/Second-Brain-Agent/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Email Notifications

Add to cron job:

```bash
MAILTO=your@email.com
0 2 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py >> logs/curator.log 2>&1
```

### Slack Notifications

Add to `schedule_curator.py`:

```python
import requests

def send_slack_notification(message):
    """Send notification to Slack"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={'text': message})

# After run completes:
send_slack_notification(f"Curator Agent: {success_count} repos ingested, {skipped_count} skipped")
```

## Best Practices

### 1. Environment Setup

Create a wrapper script `run_curator.sh`:

```bash
#!/bin/bash
set -e

# Activate virtual environment
source /path/to/venv/bin/activate

# Set environment variables
export GOOGLE_API_KEY="your_key_here"

# Change to project directory
cd /path/to/Second-Brain-Agent

# Run curator with logging
python schedule_curator.py "$@" >> logs/curator-$(date +%Y%m%d).log 2>&1
```

Then in cron:
```bash
0 2 * * * /path/to/run_curator.sh
```

### 2. Lock Files

Prevent concurrent runs:

```bash
#!/bin/bash
LOCKFILE=/tmp/curator.lock

if [ -f $LOCKFILE ]; then
    echo "Curator is already running"
    exit 1
fi

trap "rm -f $LOCKFILE" EXIT
touch $LOCKFILE

python schedule_curator.py
```

### 3. Health Checks

Monitor scheduler health:

```python
# healthcheck.py
from pathlib import Path
from datetime import datetime, timedelta

log_file = Path('logs/curator.log')
if log_file.exists():
    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
    if datetime.now() - mtime > timedelta(days=2):
        print("WARNING: Curator hasn't run in 2 days!")
```

### 4. Resource Limits

Limit memory and CPU usage:

```bash
# In cron
0 2 * * * ulimit -v 4000000 && python schedule_curator.py
```

Or in systemd service:
```ini
[Service]
MemoryLimit=4G
CPUQuota=50%
```

## Troubleshooting

### Cron not running?

```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog

# Test cron entry manually
cd /path/to/Second-Brain-Agent && python schedule_curator.py
```

### Environment variables not working?

Cron runs with minimal environment. Use:

```bash
# In crontab, set PATH explicitly
PATH=/usr/local/bin:/usr/bin:/bin
GOOGLE_API_KEY=your_key

# Or source .env in wrapper script
source .env && python schedule_curator.py
```

### Permission denied?

```bash
# Make scripts executable
chmod +x schedule_curator.py
chmod +x run_curator.sh

# Check file ownership
ls -la schedule_curator.py
```

## Recommended Schedules

| Use Case | Schedule | Cron Expression |
|----------|----------|-----------------|
| **Daily Discovery** | 2 AM daily | `0 2 * * *` |
| **Weekly Update** | Sundays 3 AM | `0 3 * * 0` |
| **Frequent Updates** | Every 6 hours | `0 */6 * * *` |
| **Monthly Full Scan** | 1st of month, midnight | `0 0 1 * *` |
| **Business Hours Only** | Weekdays 9 AM | `0 9 * * 1-5` |

## Next Steps

1. **Test manually**: `python schedule_curator.py --discover-only`
2. **Setup cron job**: Choose your schedule
3. **Monitor logs**: Check `/logs/curator.log`
4. **Verify ingestion**: Check ChromaDB collections
5. **Adjust schedule**: Based on your needs

---

For more information, see the main [CURATOR_AGENT.md](CURATOR_AGENT.md) documentation.