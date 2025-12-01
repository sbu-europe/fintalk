from rest_framework import serializers


class OpenAIMessageSerializer(serializers.Serializer):
    """
    Serializer for individual OpenAI message objects.
    
    Validates message structure with role and content fields.
    """
    role = serializers.ChoiceField(
        choices=['system', 'user', 'assistant'],
        required=True,
        help_text="Message role (system, user, or assistant)"
    )
    content = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Message content"
    )


class OpenAIQuerySerializer(serializers.Serializer):
    """
    Serializer for OpenAI Chat Completions API request.
    
    Validates the complete request including messages array and optional parameters.
    """
    model = serializers.CharField(
        required=False,
        default='amazon.nova-lite-v1:0',
        help_text="Model identifier (ignored, uses configured Bedrock model)"
    )
    messages = OpenAIMessageSerializer(
        many=True,
        required=True,
        help_text="Array of message objects with role and content"
    )
    temperature = serializers.FloatField(
        required=False,
        default=0.7,
        min_value=0.0,
        max_value=2.0,
        help_text="Sampling temperature (0.0 to 2.0)"
    )
    max_tokens = serializers.IntegerField(
        required=False,
        default=2048,
        min_value=1,
        max_value=4096,
        help_text="Maximum tokens in response"
    )
    stream = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to stream the response using Server-Sent Events"
    )
    
    def validate_messages(self, messages):
        """Ensure at least one message exists"""
        if not messages:
            raise serializers.ValidationError("At least one message is required")
        return messages


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
