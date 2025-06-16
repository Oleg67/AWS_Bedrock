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


# Make Bedrock KB
This Python script automates the creation and management of an AWS Bedrock Knowledge Base for storing and indexing PDF files from an S3 bucket. It uses the AWS SDK (boto3) to interact with Bedrock services, sets up a knowledge base with a vector-based configuration, creates a data source linked to an S3 bucket, and monitors the ingestion process. Below is a detailed description of the script:
## Key Components and Functionality:
Imports and Setup:
Libraries:
boto3: For interacting with AWS services (Bedrock and Bedrock Agent).

os: For accessing environment variables.

logging: For logging script activity to stdout.

sys: For configuring the logging stream.

botocore.exceptions.ClientError: For handling AWS-specific errors.

dotenv: For loading environment variables from a .env file.

## Logging Configuration:
Configures logging to output to stdout with a timestamp, level, and message format.

Uses a logger named after the module (__name__) for consistent logging.

Environment Variables:
Loads variables from a .env file using load_dotenv().

Expects AWS_REGION to be set for AWS service interactions.

AWS Session and Clients:
Initializes a boto3.Session with the region specified in the AWS_REGION environment variable.

Creates two clients:
bedrock: For general Bedrock operations.

bedrock_agent: For managing Bedrock Knowledge Base and data sources.

Function: create_knowledge_base(bucket_name, role_arn):
Purpose: Creates a Bedrock Knowledge Base, associates it with an S3 bucket as a data source, and starts an ingestion job to index PDF files.

## Steps:
Create Knowledge Base:
Calls bedrock_agent.create_knowledge_base to create a knowledge base named "pdf-knowledge-base."

Configures it as a VECTOR type with the amazon.titan-embed-text-v2:0 embedding model.

Uses OPENSEARCH_SERVERLESS for storage, with a vector index named "pdf-vector-index" and predefined field mappings (embedding, text, metadata).

Logs the created Knowledge Base ID.

## Create Data Source:
Calls bedrock_agent.create_data_source to link an S3 bucket (specified by bucket_name) to the knowledge base.

Configures the data source to include files under the pdfs/ prefix in the bucket.

Logs the created Data Source ID.

## Start Ingestion Job:
Calls bedrock_agent.start_ingestion_job to begin indexing the PDF files from the S3 bucket.

Logs the Ingestion Job ID.

Return Values: Returns the Knowledge Base ID (kb_id), Data Source ID (ds_id), and Ingestion Job ID (job_id).

Error Handling: Catches ClientError exceptions, logs the error, and re-raises it.

Function: check_ingestion_status(kb_id, ds_id, job_id):
Purpose: Checks the status of an ingestion job for a given knowledge base and data source.

Steps:
Calls bedrock_agent.get_ingestion_job to retrieve the job status.

Logs and returns the status (e.g., "RUNNING," "COMPLETE," "FAILED," "STOPPED").

Error Handling: Catches ClientError exceptions, logs the error, and re-raises it.

Main Execution:
Environment Setup:
Hardcodes the S3 bucket name (bedrock-kb-pdfs-123456789012-eu-north-1), IAM role ARN (arn:aws:iam::311410995876:role/SageMaker-MLengineer), and AWS region (eu-north-1).

Note: These values are placeholders and should be replaced with actual values or sourced from environment variables for security.

```bash
# Create Bucket

aws s3 mb s3://bedrock-kb-pdfs-$(aws sts get-caller-identity --query Account --output text)-eu-north-1 --region eu-north-1

# Upload PDF Files

aws s3 cp ./pdfs/ s3://bedrock-kb-pdfs-123456789012-eu-north-1/pdfs/ --recursive --region eu-north-1
```

## Execution Flow:
Calls create_knowledge_base to set up the knowledge base, data source, and ingestion job.

Enters a loop to check the ingestion job status every 30 seconds using check_ingestion_status.

Exits the loop when the job status is "COMPLETE," "FAILED," or "STOPPED."

Dependencies:
AWS Services:
AWS Bedrock and Bedrock Agent for knowledge base management.

Amazon S3 for storing PDF files.

AWS IAM role with permissions for Bedrock and S3 access.

Python Libraries: boto3, python-dotenv.

Environment Variables:
AWS_REGION: AWS region (e.g., eu-north-1).

The script also expects a .env file for loading environment variables.

Assumptions and Notes:
Placeholder Values: The bucket name and role ARN are hardcoded and should be replaced with actual values or loaded securely from environment variables.

AWS Credentials: The script assumes AWS credentials are configured (e.g., via AWS CLI, environment variables, or IAM roles).

Embedding Model: Uses amazon.titan-embed-text-v2:0 for vector embeddings, which must be available in the specified region.

OpenSearch Serverless: The script assumes an OpenSearch Serverless collection will be created automatically, as collectionArn is left empty.

Ingestion Monitoring: The script polls the ingestion job status every 30 seconds, which may need adjustment based on the volume of data or use case.

Error Handling: Robustly logs errors but re-raises them, requiring external handling (e.g., in a production environment).

Use Case:
This script is designed to automate the setup of an AWS Bedrock Knowledge Base for indexing and querying PDF files stored in an S3 bucket. It’s useful for applications requiring searchable document repositories, such as knowledge management systems or document retrieval services. The script handles the creation, data source integration, and ingestion monitoring, making it a foundational component for building a scalable document search solution.



## Use Case:
This script is designed to provide a RESTful API for querying an AWS Bedrock Knowledge Base using a CrewAI agent. It’s suitable for applications needing to retrieve structured information from a knowledge base via a web interface, with robust logging and error handling for production use.


