import boto3
import sys
import json
import os
from flask import Flask, request, jsonify
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from typing import Any
from pydantic import Field
import logging

# Increase recursion limit (temporary workaround)
sys.setrecursionlimit(2000)

# Flask app initialization
app = Flask(__name__)

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bedrock Knowledge Base Tool
class BedrockKnowledgeBaseTool(BaseTool):
    name: str = "Bedrock Knowledge Base Search"
    description: str = "Searches an AWS Bedrock Knowledge Base for relevant information based on a query."
    knowledge_base_id: str = Field(..., description="The ID of the Bedrock Knowledge Base")
    region: str = Field(..., description="AWS region for the Bedrock client")

    def __init__(self, knowledge_base_id: str, region: str):
        super().__init__(knowledge_base_id=knowledge_base_id, region=region)
        try:
            session = boto3.Session()
            self._bedrock_client = session.client("bedrock-agent-runtime", region_name=region)
            logger.info(f"Initialized Bedrock client for region {region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise

    def _run(self, query_input: Any) -> str:
        try:
            # Handle different input types
            if isinstance(query_input, str):
                try:
                    query_dict = json.loads(query_input)
                    query = query_dict.get('query', '')
                    logger.info(f"Parsed JSON string input, extracted query: {query}")
                except json.JSONDecodeError:
                    query = query_input
            elif isinstance(query_input, dict):
                query = query_input.get('query', '') or query_input.get('description', '')
                logger.info(f"Received dict input, extracted query: {query}")
            else:
                raise ValueError(f"Invalid query type: must be string or dict, got {type(query_input)}")

            if not isinstance(query, str) or not query.strip():
                raise ValueError(f"Invalid query: must be a non-empty string, got {query}")

            response = self._bedrock_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": 5
                    }
                }
            )
            results = response.get("retrievalResults", [])
            if not results:
                logger.info(f"No results found for query: {query}, returning fallback response")
                return FALLBACK_RESPONSE
            answer = "\n".join([result["content"]["text"] for result in results])
            return answer
        except Exception as e:
            logger.error(f"Error querying Bedrock Knowledge Base: {str(e)}")
            return FALLBACK_RESPONSE

def create_search_agent(knowledge_base_id: str, region: str, llm: str):
    kb_tool = BedrockKnowledgeBaseTool(knowledge_base_id=knowledge_base_id, region=region)
    search_agent = Agent(
        role="Knowledge Base Search Agent",
        goal="Search the AWS Bedrock Knowledge Base to provide accurate answers to user queries.",
        backstory="You are an expert researcher with access to a vast knowledge base powered by AWS Bedrock.",
        tools=[kb_tool],
        verbose=False,  # Disable verbose logging
        max_iter=5,  # Limit iterations
        llm=llm,
    )
    return search_agent

def create_search_task(query: str, agent: Agent):
    return Task(
        description=f"Search the knowledge base for: {query}",
        agent=agent,
        expected_output="The exact content retrieved from the Bedrock Knowledge Base for the query."
    )

# Flask Endpoint
@app.route("/api/query", methods=["POST"])
def query_agent():
    try:
        # Get query from JSON payload
        data = request.get_json()
        if not data or "query" not in data:
            logger.error("Invalid request: Missing 'query' in request body")
            return jsonify({"error": "Missing 'query' in request body"}), 400
        
        query = data["query"]
        if not isinstance(query, str) or not query.strip():
            logger.error(f"Invalid query: {query}")
            return jsonify({"error": "Query must be a non-empty string"}), 400

        logger.info(f"Received query: {query}")

        # Get environment variables
        knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")
        region = os.getenv("AWS_REGION")
        llm = os.getenv("LLM_ID")

        # Validate environment variables
        if not all([knowledge_base_id, region, llm]):
            missing = [k for k, v in {
                "KNOWLEDGE_BASE_ID": knowledge_base_id,
                "AWS_REGION": region,
                "LLM_ID": llm
            }.items() if not v]
            logger.error(f"Missing environment variables: {missing}")
            return jsonify({"error": f"Missing environment variables: {missing}"}), 400

        # Create agent and task
        search_agent = create_search_agent(knowledge_base_id, region, llm)
        search_task = create_search_task(query, search_agent)

        # Create and run the Crew
        crew = Crew(
            agents=[search_agent],
            tasks=[search_task],
            verbose=False  # Disable verbose logging
        )
        result = crew.kickoff()

        logger.info(f"Query result: {result}")

        # Return response
        return jsonify({"query": query, "result": str(result)}), 200

    except Exception as e:
        logger.error(f"Failed to process query: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
