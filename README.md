# AWS_Bedrock

This Python script implements a Flask-based web service that integrates with AWS Bedrock Knowledge Base and the CrewAI framework to handle search queries. Here's a breakdown of its functionality:

## Key Components and Functionality:

Imports and Setup:
The script uses boto3 for AWS Bedrock integration, Flask for the web server, and crewai for agent-based task execution.

Other libraries include sys, json, os, typing, pydantic, and logging for system operations, data handling, environment variables, type checking, and logging.

The recursion limit is increased to 2000 to handle potential deep recursion (though this is noted as a temporary workaround).

Logging is configured to output to stdout with a timestamp, level, and message format.

## Bedrock Knowledge Base Tool (BedrockKnowledgeBaseTool):
A custom tool class inheriting from crewai.tools.BaseTool.

Purpose: Queries an AWS Bedrock Knowledge Base to retrieve relevant information based on a user-provided query.

Attributes:
name: "Bedrock Knowledge Base Search"

description: Describes the tool's purpose.

knowledge_base_id: The ID of the Bedrock Knowledge Base (required).

region: AWS region for the Bedrock client (required).

### Initialization:
Creates a boto3 session and initializes a Bedrock client (bedrock-agent-runtime) for the specified region.

Logs success or failure during initialization.

### Run Method (_run):
Accepts a query input (string or dict) and processes it to extract the search query.

Validates the query to ensure it's a non-empty string.

Queries the Bedrock Knowledge Base using the retrieve method, requesting up to 5 results.

Returns concatenated text from the results or a fallback response (FALLBACK_RESPONSE) if no results are found or an error occurs.

Logs errors and query details for debugging.

### Agent and Task Creation:
create_search_agent:
Creates a CrewAI Agent with the role "Knowledge Base Search Agent."

The agent uses the BedrockKnowledgeBaseTool and is configured with a goal, backstory, and parameters like llm (language model ID), verbose=False, and max_iter=5.

create_search_task:
Creates a CrewAI Task for the agent to search the knowledge base for a given query.

Specifies the expected output as the exact content retrieved from the knowledge base.

### Flask Endpoint (/api/query):
Method: POST

Purpose: Receives a JSON payload with a query field, processes it, and returns the search results.

## Workflow:
Validates the request payload to ensure it contains a non-empty query string.

Retrieves environment variables: KNOWLEDGE_BASE_ID, AWS_REGION, and LLM_ID.

Returns a 400 error if any environment variables are missing or the query is invalid.

Creates a search agent and task, then initializes a Crew with the agent and task.

Executes the task using crew.kickoff() and returns the result as JSON with a 200 status.

Catches and logs any errors, returning a 500 status with the error message.

## Main Execution:
Runs the Flask app on host 0.0.0.0 and port 5000 with debug=False.

Dependencies:
AWS Bedrock: For the knowledge base and client (boto3).

CrewAI: For agent-based task execution (Agent, Task, Crew, BaseTool).

Flask: For the web server.

### Environment Variables:
KNOWLEDGE_BASE_ID: ID of the AWS Bedrock Knowledge Base.

AWS_REGION: AWS region for the Bedrock client.

LLM_ID: Language model ID for the CrewAI agent.

### Error Handling:
Logs errors at multiple levels (Bedrock client initialization, query processing, Flask endpoint).

Returns appropriate HTTP status codes (400 for bad requests, 500 for server errors).

Uses a fallback response (FALLBACK_RESPONSE, not defined in the script) when Bedrock queries fail or return no results.

### Assumptions and Notes:
The script assumes the FALLBACK_RESPONSE variable is defined elsewhere, as it’s referenced but not included.

The LLM_ID environment variable suggests integration with a language model, but the specific model is not specified.

The script requires proper AWS credentials configured for boto3 to work.

The recursion limit increase may indicate potential issues with recursive calls in CrewAI or Bedrock interactions.

## Use Case:
This script is designed to provide a RESTful API for querying an AWS Bedrock Knowledge Base using a CrewAI agent. It’s suitable for applications needing to retrieve structured information from a knowledge base via a web interface, with robust logging and error handling for production use.


