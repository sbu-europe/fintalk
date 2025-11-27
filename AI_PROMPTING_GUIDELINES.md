# AI Prompting Guidelines for Fintalk RAG System

## Overview

This document provides guidelines for crafting effective prompts when interacting with the Fintalk RAG (Retrieval-Augmented Generation) system. The system uses AWS Bedrock's Amazon Nova Lite model with LlamaIndex ReActAgent orchestration to provide intelligent responses based on uploaded documents and credit card management operations.

## System Architecture Context

The Fintalk system consists of:
- **LlamaIndex ReActAgent**: Orchestrates tool selection and response generation
- **AWS Bedrock LLM**: Amazon Nova Lite v1.0 for text generation
- **AWS Bedrock Embeddings**: Amazon Titan Embed Text v2.0 for semantic search
- **Two Primary Tools**:
  1. Vector Retriever: Searches uploaded documents using semantic similarity
  2. Credit Card Blocker: Blocks credit cards by phone number lookup

## Agent Behavior

The ReActAgent follows this pattern:
1. **Thought**: Analyzes the user's request
2. **Action**: Selects and executes appropriate tool(s)
3. **Observation**: Processes tool results
4. **Answer**: Generates final response

## Prompting Best Practices

### 1. Document Query Prompts

When querying uploaded documents, use clear and specific language:

**Good Examples:**
```
"What are the key financial metrics in the Q3 report?"
"Summarize the risk factors mentioned in the document"
"What revenue growth is projected for 2025?"
"List all compliance requirements from the uploaded policy document"
```

**Why These Work:**
- Specific about what information is needed
- Clear scope (Q3 report, risk factors, etc.)
- Action-oriented verbs (summarize, list, what)

**Avoid:**
```
"Tell me about the document"  # Too vague
"What's in there?"            # Unclear reference
"Everything about finance"    # Too broad
```

### 2. Credit Card Management Prompts

For credit card blocking operations, include the phone number:

**Good Examples:**
```
"Block the credit card for phone number +1234567890"
"I need to block my card, my number is +1234567891"
"Please block the card associated with +1234567892"
"My card was stolen, block it for +1234567893"
```

**Why These Work:**
- Clearly states the intent (block card)
- Includes the required phone number
- Natural language that the agent can parse

**Avoid:**
```
"Block my card"                    # Missing phone number
"Card ending in 1234"              # System uses phone number, not card number
"Deactivate +1234567890"           # Less clear intent
```

### 3. Hybrid Queries

The agent can handle queries that combine document search with actions:

**Good Examples:**
```
"What does the policy say about lost cards? Also block my card +1234567890"
"Check the fraud protection guidelines and block card for +1234567891"
```

**Why These Work:**
- Clear separation of two tasks
- Provides all necessary information (phone number)
- Agent can execute both tools sequentially

### 4. Context and Specificity

Provide context when needed:

**Good Examples:**
```
"In the uploaded financial report, what was the operating margin?"
"According to the compliance document, what are the data retention requirements?"
"From the Q3 earnings call transcript, what did the CEO say about expansion plans?"
```

**Why These Work:**
- References specific documents
- Narrows search scope
- Helps agent retrieve most relevant chunks

### 5. Follow-up Questions

The agent supports conversational context:

**Good Examples:**
```
First query: "What are the main products mentioned in the document?"
Follow-up: "What are the revenue figures for those products?"
Follow-up: "How do those compare to last year?"
```

**Why These Work:**
- Builds on previous context
- Natural conversation flow
- Agent maintains conversation memory

## Prompt Patterns by Use Case

### Financial Document Analysis

```
"What are the [specific metric] in the [document type]?"
"Summarize the [section name] from the uploaded document"
"Compare [metric A] and [metric B] from the report"
"What trends are mentioned regarding [topic]?"
```

### Compliance and Policy Queries

```
"What are the requirements for [specific process]?"
"List all [type of items] mentioned in the policy"
"What does the document say about [specific topic]?"
"Are there any restrictions on [activity]?"
```

### Credit Card Operations

```
"Block the credit card for phone number [+1234567890]"
"I lost my card, please block it. My number is [+1234567890]"
"Deactivate the card associated with [+1234567890]"
```

### Multi-step Queries

```
"First, check what the policy says about [topic], then block card for [phone]"
"Search for [information] and if it mentions [condition], block [phone]"
```

## Response Streaming

The system supports two response modes:

### 1. Streaming Mode (Default)
- Tokens arrive in real-time via Server-Sent Events (SSE)
- Best for interactive user experiences
- Shows thinking process as agent works

**Request:**
```json
{
  "message": "What are the key points in the Q3 report?",
  "phone_number": "+1234567890",
  "stream": true
}
```

### 2. Non-Streaming Mode
- Complete response returned as JSON
- Includes metadata (sources, tools used, timestamp)
- Best for API integrations

**Request:**
```json
{
  "message": "What are the key points in the Q3 report?",
  "phone_number": "+1234567890",
  "stream": false
}
```

## Common Pitfalls and Solutions

### Pitfall 1: Ambiguous Queries
**Problem:** "What about the numbers?"
**Solution:** "What are the revenue numbers in the Q3 financial report?"

### Pitfall 2: Missing Required Information
**Problem:** "Block my card"
**Solution:** "Block my card for phone number +1234567890"

### Pitfall 3: Overly Complex Queries
**Problem:** "Tell me everything about all financial metrics, risks, opportunities, and strategies mentioned across all documents while also checking if there are any compliance issues and block my card if needed"
**Solution:** Break into separate queries:
1. "What are the key financial metrics in the uploaded documents?"
2. "What risks are mentioned?"
3. "Block my card for phone number +1234567890"

### Pitfall 4: Assuming Document Knowledge
**Problem:** "What did page 5 say?" (Agent doesn't have page numbers)
**Solution:** "What does the document say about [specific topic]?"

### Pitfall 5: Incorrect Phone Format
**Problem:** "Block card for 1234567890" (missing country code)
**Solution:** "Block card for +1234567890" (include + and country code)

## Advanced Prompting Techniques

### 1. Scoped Searches
```
"In the risk management section, what are the top 3 risks?"
"From the executive summary only, what are the key takeaways?"
```

### 2. Comparative Analysis
```
"Compare the Q3 and Q4 revenue figures"
"What's the difference between the old and new policy?"
```

### 3. Extraction Tasks
```
"Extract all dates mentioned in the document"
"List all company names referenced"
"What are the specific dollar amounts mentioned?"
```

### 4. Conditional Logic
```
"If the document mentions fraud, tell me the fraud prevention steps"
"Check if there are any deadlines, and list them if found"
```

## Optimization Tips

### For Better Document Retrieval:
1. Use specific terminology from your domain
2. Reference document types when known
3. Ask focused questions rather than broad ones
4. Use keywords that likely appear in the document

### For Better Agent Performance:
1. One clear intent per query (or clearly separated intents)
2. Provide all required parameters (like phone numbers)
3. Use natural language - the agent is trained on conversational text
4. Be specific about what format you want (list, summary, comparison, etc.)

### For Faster Responses:
1. Avoid asking for exhaustive information
2. Limit scope to specific sections or topics
3. Use streaming mode for real-time feedback
4. Break complex queries into simpler ones

## Error Handling

The system provides clear error messages:

### Document Not Found
```
Query: "What does the 2026 report say?"
Response: "I don't have access to a 2026 report in the uploaded documents."
```

### Invalid Phone Number
```
Query: "Block card for 123"
Response: "No cardholder found with phone number: 123"
```

### Service Errors
```
Response: "I'm experiencing technical difficulties. Please try again."
```

## Testing Your Prompts

Before deploying prompts in production:

1. **Test with sample documents**: Upload test documents and verify retrieval accuracy
2. **Test edge cases**: Try queries with missing information, ambiguous language
3. **Test multi-step flows**: Ensure agent handles complex queries correctly
4. **Test error scenarios**: Verify graceful handling of invalid inputs
5. **Test streaming vs non-streaming**: Ensure both modes work as expected

## Example Conversation Flows

### Flow 1: Document Analysis
```
User: "What are the main products in the uploaded document?"
Agent: "Based on the document, the main products are: Product A, Product B, and Product C..."

User: "What's the revenue for Product A?"
Agent: "According to the document, Product A generated $5.2M in revenue..."

User: "How does that compare to Product B?"
Agent: "Product B generated $4.8M, which is $400K less than Product A..."
```

### Flow 2: Security Action
```
User: "I lost my credit card"
Agent: "I can help you block your card. Please provide your phone number."

User: "It's +1234567890"
Agent: "Successfully blocked credit card for phone number +1234567890. Card ending in: 9010. Username: john_doe. Blocked at: 2024-11-26T10:30:45Z"
```

### Flow 3: Policy Check + Action
```
User: "What does the policy say about lost cards?"
Agent: "According to the policy, if you lose your card, you should immediately report it and request a block..."

User: "Okay, block my card for +1234567890"
Agent: "Successfully blocked credit card for phone number +1234567890..."
```

## Model-Specific Considerations

### Amazon Nova Lite v1.0 Characteristics:
- **Strengths**: Fast response times, cost-effective, good at following instructions
- **Optimal for**: Straightforward queries, clear instructions, factual retrieval
- **Limitations**: May struggle with highly nuanced or ambiguous queries

### Amazon Titan Embed Text v2.0 Characteristics:
- **Vector dimensions**: 1024
- **Optimal for**: Semantic similarity, finding related concepts
- **Best practices**: Use natural language, include context keywords

## Monitoring and Improvement

Track these metrics to improve prompting:
1. **Retrieval accuracy**: Are the right documents being found?
2. **Tool selection accuracy**: Is the agent choosing the right tool?
3. **Response quality**: Are answers complete and accurate?
4. **Error rates**: How often do queries fail?
5. **User satisfaction**: Are users getting what they need?

## Conclusion

Effective prompting for the Fintalk RAG system requires:
- Clear, specific language
- Appropriate context and scope
- Required parameters (like phone numbers)
- Understanding of agent capabilities and limitations
- Iterative refinement based on results

By following these guidelines, you can maximize the effectiveness of the Fintalk RAG system and provide users with accurate, helpful responses.

## Additional Resources

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [AWS Bedrock Best Practices](https://docs.aws.amazon.com/bedrock/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- Project Context: See `project-context.md` for technical details
- API Documentation: See `README.md` for endpoint specifications
