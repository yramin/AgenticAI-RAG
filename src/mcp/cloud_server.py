"""Cloud storage MCP server."""

import logging
from typing import Any, Dict

try:
    from mcp.types import Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    class Tool:
        def __init__(self, **kwargs):
            pass

from src.mcp.mcp_server import BaseMCPServer
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class CloudMCPServer(BaseMCPServer):
    """MCP server for cloud storage operations."""

    def __init__(self):
        """Initialize cloud MCP server."""
        super().__init__("cloud_storage_server")
        self.settings = get_settings()
        self._init_cloud_client()
        self._register_tools()

    def _init_cloud_client(self):
        """Initialize cloud storage client."""
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
            except Exception as e:
                logger.error(f"Error initializing S3: {e}")

        # Check for GCS
        elif self.settings.google_application_credentials and self.settings.gcs_bucket_name:
            try:
                from google.cloud import storage
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.google_application_credentials
                self.client = storage.Client()
                self.cloud_type = "gcs"
                self.bucket_name = self.settings.gcs_bucket_name
            except Exception as e:
                logger.error(f"Error initializing GCS: {e}")

    def _register_tools(self):
        """Register cloud storage tools."""
        if not self.client:
            logger.warning("No cloud storage configured, skipping tool registration")
            return

        # List objects tool
        list_tool = Tool(
            name="list_cloud_objects",
            description="List objects in cloud storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Object key prefix to filter",
                    },
                    "max_keys": {
                        "type": "integer",
                        "description": "Maximum number of objects to return",
                        "default": 10,
                    },
                },
            },
        )
        self.register_tool(list_tool)

        # Get object tool
        get_tool = Tool(
            name="get_cloud_object",
            description="Get an object from cloud storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Object key",
                    },
                },
                "required": ["key"],
            },
        )
        self.register_tool(get_tool)

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a cloud storage tool."""
        if not self.client:
            return {"error": "Cloud storage not configured"}

        if name == "list_cloud_objects":
            prefix = arguments.get("prefix", "")
            max_keys = arguments.get("max_keys", 10)

            if self.cloud_type == "s3":
                response = self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys,
                )
                objects = [
                    {"key": obj["Key"], "size": obj["Size"]}
                    for obj in response.get("Contents", [])
                ]
                return {"objects": objects, "count": len(objects)}

            elif self.cloud_type == "gcs":
                bucket = self.client.bucket(self.bucket_name)
                blobs = list(bucket.list_blobs(prefix=prefix, max_results=max_keys))
                objects = [{"key": blob.name, "size": blob.size} for blob in blobs]
                return {"objects": objects, "count": len(objects)}

        elif name == "get_cloud_object":
            key = arguments.get("key")

            if self.cloud_type == "s3":
                try:
                    response = self.client.get_object(Bucket=self.bucket_name, Key=key)
                    content = response["Body"].read().decode("utf-8")
                    return {"key": key, "content": content}
                except Exception as e:
                    return {"error": str(e)}

            elif self.cloud_type == "gcs":
                try:
                    bucket = self.client.bucket(self.bucket_name)
                    blob = bucket.blob(key)
                    content = blob.download_as_text()
                    return {"key": key, "content": content}
                except Exception as e:
                    return {"error": str(e)}

        else:
            raise ValueError(f"Unknown tool: {name}")

