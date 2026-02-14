import logging
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from typing import Optional
import io
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Uploader:
    """Service for uploading files to AWS S3 or Cloudflare R2 (S3-compatible)"""

    def __init__(self):
        # Configuration for S3 client
        client_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': settings.AWS_S3_REGION_NAME
        }

        # Add endpoint URL for R2 or custom S3 endpoint
        if settings.AWS_S3_ENDPOINT_URL:
            client_config['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
            self.storage_type = 'r2'
            logger.info(f"Using Cloudflare R2 storage: {settings.AWS_S3_ENDPOINT_URL}")
        else:
            self.storage_type = 's3'
            logger.info("Using AWS S3 storage")

        self.s3_client = boto3.client('s3', **client_config)
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_file(
        self,
        file_obj: io.BytesIO,
        file_name: str,
        content_type: str = 'application/octet-stream'
    ) -> Optional[str]:
        """
        Upload file to S3/R2 and return the URL

        Args:
            file_obj: File-like object to upload
            file_name: Name for the file in S3/R2
            content_type: MIME type of the file

        Returns:
            URL of the uploaded file or None if failed
        """
        try:
            # Generate unique file path
            timestamp = datetime.now().strftime('%Y/%m/%d')
            s3_key = f"domain-intelligence/{timestamp}/{file_name}"

            # Extra args for upload
            extra_args = {
                'ContentType': content_type,
            }

            # For AWS S3, add ACL for public read
            # R2 doesn't support ACL in the same way
            if self.storage_type == 's3':
                extra_args['ACL'] = 'public-read'

            # Upload to S3/R2
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )

            # Generate URL based on storage type
            url = self._generate_url(s3_key)
            logger.info(f"Successfully uploaded {file_name} to {self.storage_type.upper()}: {url}")
            return url

        except ClientError as e:
            logger.error(f"Failed to upload {file_name} to {self.storage_type.upper()}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading {file_name}: {str(e)}")
            return None

    def _generate_url(self, s3_key: str) -> str:
        """Generate presigned URL for uploaded file (valid for 7 days)"""
        try:
            # Generate presigned URL (works for both R2 and S3)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=604800  # 7 days in seconds
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            # Fallback to direct URL (may not work if bucket is private)
            if self.storage_type == 'r2':
                endpoint = settings.R2_ENDPOINT.replace('https://', '').replace('http://', '')
                return f"https://{endpoint}/{self.bucket_name}/{s3_key}"
            else:
                return f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"

    def upload_pdf(self, pdf_buffer: io.BytesIO, domain_name: str) -> Optional[str]:
        """Upload PDF file to S3/R2"""
        file_name = f"{domain_name.replace('.', '_')}_report.pdf"
        return self.upload_file(pdf_buffer, file_name, 'application/pdf')

    def upload_json(self, json_buffer: io.BytesIO, domain_name: str) -> Optional[str]:
        """Upload JSON file to S3/R2"""
        file_name = f"{domain_name.replace('.', '_')}_data.json"
        return self.upload_file(json_buffer, file_name, 'application/json')

    def generate_presigned_url_from_key(self, s3_key: str, expires_in: int = 604800) -> Optional[str]:
        """
        Generate a fresh presigned URL for an existing S3/R2 object

        Args:
            s3_key: The S3 key of the file
            expires_in: URL expiration time in seconds (default: 7 days)

        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
            return None

    def delete_file(self, url: str) -> bool:
        """Delete file from S3/R2"""
        try:
            # Extract key from URL
            if 'r2.cloudflarestorage.com' in url or self.storage_type == 'r2':
                # For R2 URL format
                parts = url.split(f"{self.bucket_name}/")
                key = parts[-1] if len(parts) > 1 else url.split('/')[-1]
            else:
                # For S3 URL format
                key = url.split(f"{self.bucket_name}.s3.amazonaws.com/")[-1]

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted {key} from {self.storage_type.upper()}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from {self.storage_type.upper()}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {str(e)}")
            return False
