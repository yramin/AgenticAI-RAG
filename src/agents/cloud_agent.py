"""Cloud storage agent for remote data access."""

import logging
import os
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class CloudAgent(BaseAgent):
    """Agent specialized in accessing cloud storage and remote data."""

    def __init__(self, use_planning: bool = False):
        """Initialize cloud agent."""
        super().__init__(
            name="cloud_agent",
            description=(
                "You are a specialized agent for accessing cloud storage and remote data. "
                "You can retrieve documents and information from cloud storage services "
                "like AWS S3 or Google Cloud Storage."
            ),
            use_memory=True,
            use_planning=use_planning,
        )
        self.settings = get_settings()
        self._init_cloud_client()

    def _init_cloud_client(self):
        """Initialize cloud storage client based on configuration."""
        self.cloud_type = None
        self.client = None

        # Check for AWS S3
        if self.settings.aws_access_key_id and self.settings.aws_s3_bucket:
            try:
                import boto3
                self.client = boto3.client(
                    "s3",
                    aws_access_key_id=self.settings.aws_access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key,
                    region_name=self.settings.aws_region,
                )
                self.cloud_type = "s3"
                self.bucket_name = self.settings.aws_s3_bucket
                logger.info("Initialized AWS S3 client")
            except ImportError:
                logger.warning("boto3 not installed, AWS S3 unavailable")
            except Exception as e:
                logger.error(f"Error initializing S3 client: {e}")

        # Check for GCS
        elif self.settings.google_application_credentials and self.settings.gcs_bucket_name:
            try:
                from google.cloud import storage
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.google_application_credentials
                self.client = storage.Client()
                self.cloud_type = "gcs"
                self.bucket_name = self.settings.gcs_bucket_name
                logger.info("Initialized Google Cloud Storage client")
            except ImportError:
                logger.warning("google-cloud-storage not installed, GCS unavailable")
            except Exception as e:
                logger.error(f"Error initializing GCS client: {e}")

        if not self.client:
            logger.warning("No cloud storage configured")

    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from cloud storage.

        Args:
            query: User query

        Returns:
            Context string from cloud documents
        """
        if not self.client:
            return "Cloud storage is not configured."

        try:
            if self.cloud_type == "s3":
                return await self._retrieve_from_s3(query)
            elif self.cloud_type == "gcs":
                return await self._retrieve_from_gcs(query)
            else:
                return "Unknown cloud storage type."
        except Exception as e:
            logger.error(f"Error retrieving cloud context: {e}")
            return f"Error retrieving from cloud storage: {str(e)}"

    async def _retrieve_from_s3(self, query: str) -> str:
        """Retrieve documents from S3."""
        try:
            # List objects in bucket (simplified - in production, use vector search)
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=10,
            )

            if "Contents" not in response:
                return "No documents found in S3 bucket."

            context_parts = [f"Documents in S3 bucket '{self.bucket_name}':"]
            for obj in response["Contents"][:5]:  # Limit to 5
                key = obj["Key"]
                size = obj["Size"]
                context_parts.append(f"- {key} ({size} bytes)")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            return f"Error accessing S3: {str(e)}"

    async def _retrieve_from_gcs(self, query: str) -> str:
        """Retrieve documents from GCS."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blobs = list(bucket.list_blobs(max_results=10))

            if not blobs:
                return "No documents found in GCS bucket."

            context_parts = [f"Documents in GCS bucket '{self.bucket_name}':"]
            for blob in blobs[:5]:  # Limit to 5
                context_parts.append(f"- {blob.name} ({blob.size} bytes)")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error listing GCS objects: {e}")
            return f"Error accessing GCS: {str(e)}"

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Process query with cloud storage access.

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context

        Returns:
            Response dictionary
        """
        # Retrieve cloud context
        cloud_context = await self.retrieve_context(query)

        # Combine with provided context
        full_context = cloud_context
        if context:
            full_context = f"{context}\n\n{cloud_context}"

        # Process using base agent
        return await super().process(query, session_id, full_context)

