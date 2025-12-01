#!/bin/bash

# Test script for OpenAI-compatible endpoint
# Usage: ./test_openai_endpoint.sh [base_url]
# Example: ./test_openai_endpoint.sh http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
ENDPOINT="${BASE_URL}/api/chat/completions/"

echo "=========================================="
echo "Testing OpenAI-Compatible Endpoint"
echo "=========================================="
echo "Endpoint: $ENDPOINT"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Basic query (non-streaming)
echo -e "${YELLOW}Test 1: Basic Query (Non-Streaming)${NC}"
echo "Request: Simple user message"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, what services do you offer?"}
    ],
    "stream": false
  }')

if echo "$RESPONSE" | grep -q '"object":"chat.completion"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Valid OpenAI response format"
  echo "Response ID: $(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)"
else
  echo -e "${RED}✗ FAILED${NC} - Invalid response format"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 2: Query with system prompt (non-streaming)
echo -e "${YELLOW}Test 2: Query with System Prompt (Non-Streaming)${NC}"
echo "Request: System message + user message"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful banking assistant."},
      {"role": "user", "content": "What loan options are available?"}
    ],
    "temperature": 0.7,
    "stream": false
  }')

if echo "$RESPONSE" | grep -q '"role":"assistant"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Response contains assistant message"
  TOKENS=$(echo "$RESPONSE" | grep -o '"total_tokens":[0-9]*' | cut -d':' -f2)
  echo "Total tokens: $TOKENS"
else
  echo -e "${RED}✗ FAILED${NC} - Invalid response"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 3: Phone number extraction
echo -e "${YELLOW}Test 3: Phone Number Extraction${NC}"
echo "Request: Message with phone number"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I need help with my account [phone: +1234567890]"}
    ]
  }')

if echo "$RESPONSE" | grep -q '"object":"chat.completion"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Phone number processed successfully"
else
  echo -e "${RED}✗ FAILED${NC} - Phone number processing failed"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 4: Multi-turn conversation
echo -e "${YELLOW}Test 4: Multi-turn Conversation${NC}"
echo "Request: Conversation history"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What loan options do you have?"},
      {"role": "assistant", "content": "We offer personal loans, home loans, and auto loans."},
      {"role": "user", "content": "Tell me more about personal loans"}
    ]
  }')

if echo "$RESPONSE" | grep -q '"finish_reason":"stop"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Multi-turn conversation handled"
else
  echo -e "${RED}✗ FAILED${NC} - Conversation handling failed"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 5: Invalid request (missing messages)
echo -e "${YELLOW}Test 5: Error Handling (Missing Messages)${NC}"
echo "Request: Invalid request without messages"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo"
  }')

if echo "$RESPONSE" | grep -q '"error"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Error response returned"
  ERROR_TYPE=$(echo "$RESPONSE" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)
  echo "Error type: $ERROR_TYPE"
else
  echo -e "${RED}✗ FAILED${NC} - Should return error"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 6: Invalid role
echo -e "${YELLOW}Test 6: Error Handling (Invalid Role)${NC}"
echo "Request: Invalid message role"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "invalid_role", "content": "Test message"}
    ]
  }')

if echo "$RESPONSE" | grep -q '"error"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Invalid role rejected"
else
  echo -e "${RED}✗ FAILED${NC} - Should reject invalid role"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 7: Temperature validation
echo -e "${YELLOW}Test 7: Parameter Validation (Temperature)${NC}"
echo "Request: Valid temperature parameter"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Test"}
    ],
    "temperature": 0.5,
    "max_tokens": 1024
  }')

if echo "$RESPONSE" | grep -q '"object":"chat.completion"'; then
  echo -e "${GREEN}✓ PASSED${NC} - Parameters accepted"
else
  echo -e "${RED}✗ FAILED${NC} - Parameter validation failed"
  echo "Response: $RESPONSE"
fi
echo ""

# Test 8: Streaming support
echo -e "${YELLOW}Test 8: Streaming Support${NC}"
echo "Request: Stream parameter set to true"
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Test"}
    ],
    "stream": true
  }' | head -n 5)

if echo "$RESPONSE" | grep -q 'data:'; then
  echo -e "${GREEN}✓ PASSED${NC} - Streaming response received"
  echo "First few lines of stream:"
  echo "$RESPONSE" | head -n 2
else
  echo -e "${RED}✗ FAILED${NC} - Streaming not working"
  echo "Response: $RESPONSE"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "All tests completed. Review results above."
echo ""
echo "Next steps:"
echo "1. If all tests passed, the endpoint is ready for Vapi.ai integration"
echo "2. Deploy to production with HTTPS enabled"
echo "3. Configure Vapi.ai with: https://your-domain.com/api/chat/completions/"
echo "4. See VAPI_INTEGRATION.md for detailed integration guide"
echo ""
