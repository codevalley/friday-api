# S3 Storage Configuration Guide

This guide explains how to configure the document storage system to use S3-compatible storage backends.

## Overview

The document storage system supports multiple storage backends, including S3-compatible storage services like:
- Amazon S3
- MinIO
- DigitalOcean Spaces
- Backblaze B2
- Any other S3-compatible service

## Configuration

### Environment Variables

Set the following environment variables to configure S3 storage:

```bash
# Set storage backend to S3
STORAGE_BACKEND=s3

# Required S3 configuration
S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional S3 configuration
S3_ENDPOINT_URL=https://your-s3-endpoint  # Required for non-AWS S3-compatible services
AWS_REGION=us-east-1                      # Defaults to us-east-1
```

### Bucket Configuration

1. Create an S3 bucket with the following settings:
   - Enable versioning (recommended)
   - Configure CORS if needed for browser uploads
   - Set appropriate bucket policies

2. Create an IAM user/access key with the following permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:PutObject",
                   "s3:GetObject",
                   "s3:DeleteObject",
                   "s3:ListBucket"
               ],
               "Resource": [
                   "arn:aws:s3:::your-bucket-name",
                   "arn:aws:s3:::your-bucket-name/*"
               ]
           }
       ]
   }
   ```

## Example Configurations

### Amazon S3

```bash
STORAGE_BACKEND=s3
S3_BUCKET_NAME=my-app-documents
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION=us-west-2
```

### MinIO

```bash
STORAGE_BACKEND=s3
S3_BUCKET_NAME=documents
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_REGION=us-east-1
```

### DigitalOcean Spaces

```bash
STORAGE_BACKEND=s3
S3_BUCKET_NAME=my-space
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
AWS_ACCESS_KEY_ID=your-spaces-key
AWS_SECRET_ACCESS_KEY=your-spaces-secret
AWS_REGION=nyc3
```

## Security Best Practices

1. **Access Keys**:
   - Never commit access keys to version control
   - Rotate access keys regularly
   - Use environment-specific keys (dev/staging/prod)

2. **Bucket Policy**:
   - Follow the principle of least privilege
   - Enable bucket versioning for recovery
   - Enable server-side encryption
   - Configure appropriate CORS policies

3. **Monitoring**:
   - Enable access logging
   - Set up alerts for unusual activity
   - Monitor storage costs

## Troubleshooting

Common issues and solutions:

1. **Connection Timeout**:
   - Check if endpoint URL is correct
   - Verify network connectivity
   - Check firewall rules

2. **Access Denied**:
   - Verify access key and secret
   - Check bucket permissions
   - Ensure IAM policy is correct

3. **Invalid Endpoint**:
   - Ensure endpoint URL includes protocol (http/https)
   - Check if region is correct
   - Verify service endpoint format
