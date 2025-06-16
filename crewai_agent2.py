import os
import json
import boto3
import requests
from typing import Dict, List, Any
from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool
from langchain.llms.bedrock import Bedrock

# Initialize AWS Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Initialize Bedrock LLM
bedrock_llm = Bedrock(
    model_id="anthropic.claude-v2",  # or your preferred model
    client=bedrock_runtime,
    model_kwargs={
        "temperature": 0.2,
        "max_tokens_to_sample": 4000
    }
)

# Initialize Bedrock Knowledge Base client
bedrock_kb = boto3.client(
    service_name="bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Riskwolf API tools
def call_metadata_api(query: str) -> Dict:
    """Call the Riskwolf Metadata API to retrieve metadata information."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"https://api.riskwolf.com/v1/metadata?query={query}",
        headers=headers
    )
    return response.json()

def call_validate_api(config: Dict) -> Dict:
    """Call the Riskwolf Validate API to validate coverage configurations."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(
        "https://api.riskwolf.com/v1/validate",
        headers=headers,
        json=config
    )
    return response.json()

def call_index_values_api(index_id: str, params: Dict) -> Dict:
    """Call the Riskwolf Index Values API to get index values."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"https://api.riskwolf.com/v1/indices/{index_id}/values",
        headers=headers,
        params=params
    )
    return response.json()

def build_coverage_tool(params: Dict) -> Dict:
    """Use the Build Coverage/Burn Cost Tool to create coverage options."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(
        "https://api.riskwolf.com/v1/coverage/build",
        headers=headers,
        json=params
    )
    return response.json()

def configure_coverage_api(config: Dict) -> Dict:
    """Use the Coverage Config Tool/API to configure coverage details."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(
        "https://api.riskwolf.com/v1/coverage/configure",
        headers=headers,
        json=config
    )
    return response.json()

def query_world_event_db(query: str) -> Dict:
    """Query the World Event/Coverage Database."""
    api_key = os.environ.get("RISKWOLF_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        f"https://api.riskwolf.com/v1/events?query={query}",
        headers=headers
    )
    return response.json()

def query_bedrock_kb(query: str) -> str:
    """Query the Amazon Bedrock Knowledge Base."""
    response = bedrock_kb.retrieve(
        knowledgeBaseId=os.environ.get("BEDROCK_KB_ID"),
        retrievalQuery={
            "text": query
        },
        numberOfResults=5
    )
    
    results = []
    for result in response.get('retrievalResults', []):
        results.append({
            'content': result.get('content', {}).get('text', ''),
            'score': result.get('score', 0)
        })
    
    return json.dumps(results, indent=2)

def parse_paramxel_docs(query: str) -> str:
    """Parse paramXEL documentation for relevant information."""
    # This would typically call a service that parses paramXEL docs
    # For this example, we'll simulate with a Bedrock KB query
    return query_bedrock_kb(f"paramXEL documentation for {query}")

# Define tools
tools = [
    Tool(
        name="Metadata API",
        func=call_metadata_api,
        description="Get metadata information from Riskwolf"
    ),
    Tool(
        name="Validate API",
        func=call_validate_api,
        description="Validate coverage configurations"
    ),
    Tool(
        name="Index Values API",
        func=call_index_values_api,
        description="Get index values from Riskwolf"
    ),
    Tool(
        name="Build Coverage Tool",
        func=build_coverage_tool,
        description="Build coverage options and calculate burn cost"
    ),
    Tool(
        name="Coverage Config API",
        func=configure_coverage_api,
        description="Configure coverage details"
    ),
    Tool(
        name="World Event Database",
        func=query_world_event_db,
        description="Query the World Event/Coverage Database"
    ),
    Tool(
        name="Bedrock Knowledge Base",
        func=query_bedrock_kb,
        description="Query the Amazon Bedrock Knowledge Base"
    ),
    Tool(
        name="paramXEL Documentation",
        func=parse_paramxel_docs,
        description="Parse paramXEL documentation for relevant information"
    )
]

# Define the Agent 2 (Matcher)
matcher_agent = Agent(
    role="Coverage Matcher",
    goal="Match user requirements to optimal coverage options",
    backstory="""You are an expert in matching user requirements to the optimal 
    coverage options. You understand paramXEL documentation and can navigate 
    complex coverage configurations. Your job is to take clear definitions from 
    users and find the best matching coverage options.""",
    verbose=True,
    allow_delegation=False,
    tools=tools,
    llm=bedrock_llm
)

# Define Tasks for Plan-Do-Check-Act workflow

# PLAN Phase
planning_task = Task(
    description="""
    PLAN PHASE: Orchestrate and plan the matching process.
    
    1. Analyze the input requirements (either from user or Agent 1)
    2. Identify key parameters needed for matching
    3. Determine which APIs and tools will be needed
    4. Create a structured plan for the matching process
    
    Your output should be a JSON with:
    - requirements_analysis: summary of the key requirements
    - parameters_needed: list of parameters needed for matching
    - tools_to_use: list of tools/APIs to be used
    - matching_plan: step-by-step plan for the matching process
    """,
    expected_output="A structured matching plan in JSON format",
    agent=matcher_agent
)

# DO Phase
execution_task = Task(
    description="""
    DO PHASE: Execute the matching plan using the appropriate tools.
    
    1. Use the Metadata API to get relevant metadata
    2. Parse paramXEL documentation for configuration details
    3. Use the Build Coverage Tool to create coverage options
    4. Configure coverage details using the Coverage Config API
    
    Your output should include:
    - metadata_results: results from the Metadata API
    - paramxel_details: relevant details from paramXEL documentation
    - coverage_options: options generated by the Build Coverage Tool
    - coverage_config: configuration details
    """,
    expected_output="Results from executing the matching plan",
    agent=matcher_agent
)

# CHECK Phase
validation_task = Task(
    description="""
    CHECK PHASE: Validate and critique the matching results.
    
    1. Use the Validate API to validate the coverage configuration
    2. Check the results against the World Event Database
    3. Verify against the Bedrock Knowledge Base
    4. Critique the matching results for accuracy and completeness
    
    Your output should include:
    - validation_results: results from the Validate API
    - event_check: relevant events from the World Event Database
    - knowledge_check: verification from the Bedrock Knowledge Base
    - critique: critical evaluation of the matching results
    - pass_check: boolean indicating if the results pass validation
    """,
    expected_output="Validation results and critique",
    agent=matcher_agent
)

# ACT Phase
finalization_task = Task(
    description="""
    ACT PHASE: Finalize the matching results.
    
    If the results passed validation:
    1. Format the final coverage options
    2. Provide a summary of the matching process
    3. Include any recommendations for the user
    
    If the results did not pass validation:
    1. Identify the issues that need to be addressed
    2. Recommend changes to the matching plan
    3. Indicate that the process should return to the PLAN phase
    
    Your output should be a JSON with:
    - status: "final" or "needs_revision"
    - coverage_options: final coverage options (if status is "final")
    - summary: summary of the matching process
    - recommendations: recommendations for the user
    - issues: issues that need to be addressed (if status is "needs_revision")
    """,
    expected_output="Final matching results or revision plan",
    agent=matcher_agent
)

# Create the crew
matcher_crew = Crew(
    agents=[matcher_agent],
    tasks=[planning_task, execution_task, validation_task, finalization_task],
    verbose=2,
    process=Process.sequential  # Tasks will be executed in sequence
)

def process_input(input_text: str, source: str = "user") -> Dict[str, Any]:
    """
    Main function to process input for Agent 2 (Matcher).
    
    Args:
        input_text: The input text (either from user or Agent 1)
        source: The source of the input ("user" or "agent1")
        
    Returns:
        The matching results
    """
    # Set the input for the first task
    context = f"Input from {source}: {input_text}"
    if source == "agent1":
        context += "\nThis input comes from Agent 1 (Profiler) and contains a risk profile."
    else:
        context += "\nThis input comes directly from a user who has a clear definition of their needs."
    
    planning_task.context = context
    
    # Execute the crew workflow
    result = matcher_crew.kickoff()
    
    # Parse the final result
    try:
        final_output = json.loads(result)
    except:
        final_output = {"matching_results": result}
    
    return final_output

# Example usage
if __name__ == "__main__":
    # Example input (could be from user or Agent 1)
    sample_input = """
    I need coverage for flight delay insurance with the following parameters:
    - Coverage for flights between JFK and LAX
    - Coverage period: January 1, 2024 to March 31, 2024
    - Payout trigger: Delays of 2+ hours
    - Payout amount: $200 per incident
    - Maximum coverage: $1000 per customer
    """
    
    # Process the input
    matching_results = process_input(sample_input, source="user")
    print(json.dumps(matching_results, indent=2))
    
    # Example of processing input from Agent 1
    sample_agent1_output = """
    Risk Profile for AirTravelers Inc:
    
    Company: AirTravelers Inc
    Industry: Travel Insurance
    Primary Risk Factors:
    - Offering flight delay insurance for domestic US routes
    - Historical data shows 15% of flights delayed by 2+ hours
    - Peak delay seasons: Winter (Dec-Feb) and Summer (Jun-Aug)
    - Target customer base: Business travelers
    
    Recommended Coverage Structure:
    - Parametric trigger based on flight delay time
    - Tiered payout structure based on delay duration
    - Seasonal pricing adjustments
    - Integration with flight tracking APIs
    """
    
    # Process the input from Agent 1
    matching_results_from_agent1 = process_input(sample_agent1_output, source="agent1")
    print(json.dumps(matching_results_from_agent1, indent=2))
