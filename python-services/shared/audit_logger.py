"""
Audit Logger - Comprehensive logging for ethical compliance
Logs all user queries and AI-generated outputs for audit purposes
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
from loguru import logger


class AuditLogger:
    """
    Centralized audit logging for ethical compliance and accountability.
    
    Features:
    - Logs all user queries with timestamps
    - Logs all AI-generated outputs (predictions, opinions)
    - Structured JSON format for easy analysis
    - Configurable retention policy
    - User identifier tracking
    - Request/response correlation
    """
    
    def __init__(
        self,
        log_directory: str = None,
        retention_days: int = 90,
        enable_console_logging: bool = False
    ):
        """
        Initialize the audit logger.
        
        Args:
            log_directory: Directory for audit logs (default: ./audit_logs)
            retention_days: Number of days to retain logs
            enable_console_logging: Whether to also log to console
        """
        self.log_directory = Path(log_directory or os.getenv("AUDIT_LOG_DIR", "./audit_logs"))
        self.retention_days = retention_days
        self.enable_console_logging = enable_console_logging
        
        # Create log directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Audit logger initialized: {self.log_directory}")
    
    def log_query(
        self,
        user_id: str,
        service: str,
        endpoint: str,
        query_data: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> str:
        """
        Log a user query.
        
        Args:
            user_id: User identifier (IP, session ID, or user ID)
            service: Service name (search, prediction, opinion)
            endpoint: API endpoint called
            query_data: Query parameters and data
            request_id: Optional request correlation ID
        
        Returns:
            Request ID for correlation with response
        """
        request_id = request_id or self._generate_request_id()
        
        log_entry = {
            "type": "query",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "service": service,
            "endpoint": endpoint,
            "query_data": self._sanitize_data(query_data)
        }
        
        self._write_log(log_entry, "queries")
        
        if self.enable_console_logging:
            logger.info(f"[AUDIT] Query logged: {service}/{endpoint} by {user_id}")
        
        return request_id
    
    def log_output(
        self,
        request_id: str,
        user_id: str,
        service: str,
        output_type: str,
        output_data: Dict[str, Any],
        processing_time_ms: float = None
    ):
        """
        Log an AI-generated output.
        
        Args:
            request_id: Request correlation ID
            user_id: User identifier
            service: Service name
            output_type: Type of output (prediction, opinion, search_results)
            output_data: Generated output data
            processing_time_ms: Processing time in milliseconds
        """
        log_entry = {
            "type": "output",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "service": service,
            "output_type": output_type,
            "output_data": self._sanitize_data(output_data),
            "processing_time_ms": processing_time_ms,
            "ai_generated": True
        }
        
        self._write_log(log_entry, "outputs")
        
        if self.enable_console_logging:
            logger.info(f"[AUDIT] Output logged: {service}/{output_type} for {user_id}")
    
    def log_error(
        self,
        request_id: str,
        user_id: str,
        service: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ):
        """
        Log an error for audit purposes.
        
        Args:
            request_id: Request correlation ID
            user_id: User identifier
            service: Service name
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
        """
        log_entry = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "service": service,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace
        }
        
        self._write_log(log_entry, "errors")
        
        if self.enable_console_logging:
            logger.warning(f"[AUDIT] Error logged: {service}/{error_type} for {user_id}")
    
    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """
        Retrieve audit logs for a specific user.
        
        Args:
            user_id: User identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of audit log entries for the user
        """
        # This is a simplified implementation
        # In production, use a database for efficient querying
        logs = []
        
        for log_type in ["queries", "outputs", "errors"]:
            log_file = self._get_log_file(log_type)
            if log_file.exists():
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("user_id") == user_id:
                                entry_date = datetime.fromisoformat(entry["timestamp"])
                                
                                if start_date and entry_date < start_date:
                                    continue
                                if end_date and entry_date > end_date:
                                    continue
                                
                                logs.append(entry)
                        except json.JSONDecodeError:
                            continue
        
        return sorted(logs, key=lambda x: x["timestamp"])
    
    def cleanup_old_logs(self):
        """
        Remove audit logs older than retention period.
        """
        cutoff_date = datetime.utcnow().timestamp() - (self.retention_days * 86400)
        
        for log_file in self.log_directory.glob("*.jsonl"):
            if log_file.stat().st_mtime < cutoff_date:
                logger.info(f"Removing old audit log: {log_file}")
                log_file.unlink()
    
    def _write_log(self, log_entry: Dict, log_type: str):
        """
        Write log entry to file.
        
        Args:
            log_entry: Log entry dictionary
            log_type: Type of log (queries, outputs, errors)
        """
        log_file = self._get_log_file(log_type)
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _get_log_file(self, log_type: str) -> Path:
        """
        Get log file path for current date.
        
        Args:
            log_type: Type of log
        
        Returns:
            Path to log file
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_directory / f"{log_type}_{date_str}.jsonl"
    
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID.
        
        Returns:
            Request ID string
        """
        import uuid
        return str(uuid.uuid4())
    
    def _sanitize_data(self, data: Any) -> Any:
        """
        Sanitize data to remove sensitive information.
        
        Args:
            data: Data to sanitize
        
        Returns:
            Sanitized data
        """
        # In production, implement PII detection and redaction
        # For now, just ensure it's JSON-serializable
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)


# Singleton instance
_audit_logger_instance = None


def get_audit_logger(
    log_directory: str = None,
    retention_days: int = 90
) -> AuditLogger:
    """
    Get or create the singleton AuditLogger instance.
    
    Args:
        log_directory: Log directory (only used on first call)
        retention_days: Retention period (only used on first call)
    
    Returns:
        AuditLogger instance
    """
    global _audit_logger_instance
    
    if _audit_logger_instance is None:
        log_directory = log_directory or os.getenv("AUDIT_LOG_DIR", "./audit_logs")
        retention_days = int(os.getenv("AUDIT_RETENTION_DAYS", retention_days))
        
        _audit_logger_instance = AuditLogger(
            log_directory=log_directory,
            retention_days=retention_days
        )
    
    return _audit_logger_instance
