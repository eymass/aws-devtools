from marshmallow import Schema, fields


class AsyncJobResponseSchema(Schema):
    """202 response returned immediately when an async deployment job is queued."""
    message = fields.Str(
        metadata={
            "description": "Human-readable confirmation that the job was accepted.",
            "example": "Static deployment scheduled",
        }
    )
    jobId = fields.Str(
        metadata={
            "description": "Celery task ID. Poll GET /api/deployments/jobs/{jobId} to track progress.",
            "example": "d3b5c8ea-1f2a-4b3c-9d8e-7f6a5b4c3d2e",
        }
    )


class JobStatusResponseSchema(Schema):
    """Response from GET /jobs/{job_id}. Fields present depend on the task state."""
    state = fields.Str(
        metadata={
            "description": "Current task state. One of: PENDING, PROGRESS, SUCCESS, FAILURE.",
            "example": "SUCCESS",
        }
    )
    message = fields.Str(
        allow_none=True,
        load_default=None,
        metadata={"description": "Status message — present for PENDING and PROGRESS states."},
    )
    result = fields.Raw(
        allow_none=True,
        load_default=None,
        metadata={"description": "Task result payload — present only for SUCCESS state."},
    )
    error = fields.Str(
        allow_none=True,
        load_default=None,
        metadata={"description": "Error detail string — present only for FAILURE state."},
    )


class EnvironmentResponseSchema(Schema):
    """Generic envelope returned by ElasticBeanstalk environment operations."""
    response = fields.Raw(
        metadata={"description": "Raw AWS ElasticBeanstalk API response payload."}
    )


class DataListResponseSchema(Schema):
    """Generic list/data envelope."""
    data = fields.Raw(
        metadata={"description": "Response payload from AWS."}
    )


class DomainAvailabilityResponseSchema(Schema):
    """Returned by domain availability and ownership checks."""
    available = fields.Bool(
        allow_none=True,
        metadata={"description": "True if the domain is available for registration."},
    )
    owned = fields.Bool(
        allow_none=True,
        metadata={"description": "True if the domain is registered in the AWS account."},
    )
    domain = fields.Str(
        allow_none=True,
        metadata={"description": "The queried domain name."},
    )
    response = fields.Raw(
        allow_none=True,
        metadata={"description": "Full AWS Route 53 Domains API response."},
    )


class EnvironmentStatusResponseSchema(Schema):
    """Returned by GET /environments/status."""
    EnvironmentName = fields.Str(metadata={"description": "ElasticBeanstalk environment name."})
    Status = fields.Str(metadata={"description": "Environment status (e.g. Ready, Launching, Terminating)."})
    Health = fields.Str(metadata={"description": "Environment health color (Green, Yellow, Red, Grey)."})
    EnvironmentId = fields.Str(metadata={"description": "Unique environment ID."})
    ApplicationName = fields.Str(metadata={"description": "Parent application name."})
    CNAME = fields.Str(allow_none=True, metadata={"description": "Public CNAME for the environment."})
    EndpointURL = fields.Str(allow_none=True, metadata={"description": "Load balancer endpoint URL."})
    DateCreated = fields.Str(metadata={"description": "ISO-8601 creation timestamp."})
    DateUpdated = fields.Str(metadata={"description": "ISO-8601 last-updated timestamp."})


class EnvironmentHealthResponseSchema(Schema):
    """Returned by GET /environments/health."""
    health = fields.Raw(
        metadata={"description": "ElasticBeanstalk describe_environment_health response."}
    )
    logs = fields.Raw(
        metadata={"description": "ElasticBeanstalk retrieve_environment_logs response."}
    )


class ValidationResponseSchema(Schema):
    """Returned by GET /environments/validate."""
    response = fields.Raw(
        metadata={"description": "End-to-end validation result for environment + domain."}
    )


class ErrorResponseSchema(Schema):
    """Standard error envelope."""
    error = fields.Raw(
        metadata={"description": "Error detail or marshmallow validation messages."}
    )


class BucketResponseSchema(Schema):
    """Returned by bucket create/delete operations."""
    name = fields.Str(
        allow_none=True,
        metadata={"description": "Bucket name."},
    )
    location = fields.Str(
        allow_none=True,
        metadata={"description": "AWS region where the bucket was created."},
    )
    response = fields.Raw(
        allow_none=True,
        metadata={"description": "Raw AWS S3 API response."},
    )
