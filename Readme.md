# AWS-Devtools

AWS-Devtools is a Python package designed to streamline and simplify interactions with AWS cloud services. It provides developers with tools to quickly deploy CloudFront distributions, purchase domains, issue certificates, and handle other common tasks, connecting all the dots efficiently.

## Features

- **Deploy Full Solution**: Easily deploy CloudFront distributions and connect them to your new domains.
- **Deploy CloudFront Distribution**: Easily deploy and configure CloudFront distributions.
- **Purchase Domain**: Automate the process of purchasing domains through AWS.
- **Issue Certificates**: Simplify the issuance and management of SSL/TLS certificates.
- **Integrated Workflow**: Connect various AWS services seamlessly to streamline your development process.

## Installation

You can install AWS-Devtools using pip:

```bash
pip install -r requirements.txt
```

## Configuration

Set the required environment variables:

```bash
export CELERY_BROKER_URL="mongodb://localhost:27017/celery"  # or your MongoDB connection string
```

## Development Setup

This application uses Celery for background task processing. To run the application locally, you need to start both the Flask server and a Celery worker.

### Terminal 1 - Flask Server

```bash
python run.py
```

The server will start on port 5200 (or the port specified by the `PORT` environment variable).

### Terminal 2 - Celery Worker

**Important**: The Celery worker must be running for background tasks to execute. Without it, tasks will be queued but never processed.

```bash
celery -A celery_app.celery_app worker --loglevel=info
```

This will start the Celery worker and show detailed logs. You should see:
- Worker startup messages
- Registered tasks (including `api.deployments.deploy_domain_task_wrapped`)
- Connection to MongoDB broker
- Task execution logs when endpoints trigger background jobs

### Verifying Background Tasks

When you make a request to `/api/deployments/environments/deploy`, you should:
1. Receive an immediate response with a job ID (from the Flask server)
2. See task execution logs in the **Celery worker terminal** (not the Flask server terminal)
3. Check job status using `/api/deployments/jobs/<job_id>`

## Production Deployment

For production environments (e.g., Heroku), both web and worker processes are defined in the `Procfile`:
- `web`: Runs the Flask application
- `worker`: Runs the Celery worker for background task processing

Make sure to scale both processes appropriately
