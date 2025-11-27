from rest_framework import serializers


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for document upload requests.
    
    Validates uploaded files and ensures they are in supported formats.
    """
    file = serializers.FileField(
        required=True,
        help_text="Document file to upload (PDF, TXT, or DOCX)"
    )
    
    SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.docx']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def validate_file(self, value):
        """
        Validate the uploaded file format and size.
        
        Args:
            value: The uploaded file object
            
        Returns:
            The validated file object
            
        Raises:
            ValidationError: If file format is not supported or file is too large
        """
        import os
        
        # Get file extension
        file_name = value.name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Validate file extension
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file format '{file_ext}'. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
        
        # Validate file size
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of "
                f"{self.MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
            )
        
        return value


class AgentQuerySerializer(serializers.Serializer):
    """
    Serializer for agent query requests.
    
    Validates query messages and optional parameters for agent interactions.
    """
    message = serializers.CharField(
        required=True,
        help_text="The query message to send to the agent"
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Phone number for credit card operations (optional)"
    )
    stream = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to stream the response (default: true)"
    )
