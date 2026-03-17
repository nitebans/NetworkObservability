import requests
from langchain_ollama import OllamaLLM
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferMemory

PROM_URL = "http://localhost:9090/api/v1/query"

from langchain.prompts import PromptTemplate

system_prompt = """
You are a telecom monitoring assistant.

You can query Prometheus using the tool query_prometheus.

Available metric:
smf_active_sessions

Rules:
- Only use smf_active_sessions
- Use valid PromQL syntax
- Never invent metrics

Agent format MUST be:

Thought: explain reasoning
Action: query_prometheus
Action Input: <prometheus query>

Observation: <metric value>

Final Answer: <explain result clearly>

IMPORTANT:
After receiving Observation you MUST produce Final Answer.
Never call the tool again.
"""

# Prometheus tool
def query_prometheus(query):

    query = query.replace("`", "").strip()

    r = requests.get(PROM_URL, params={"query": query})
    resp = r.json()

    if resp["status"] != "success":
        return f"Prometheus query error: {resp}"

    data = resp["data"]["result"]

    if not data:
        return "No data returned"

    value = data[0]["value"]

    if isinstance(value, list):
        value = value[1]

    return value


prometheus_tool = Tool(
    name="query_prometheus",
    func=query_prometheus,
    description="""
Query Prometheus metrics.

Available metric:
smf_active_sessions

Examples:
smf_active_sessions
smf_active_sessions offset 10m

Output rule:
When the tool returns a number, immediately respond:

Final Answer: <number>

Do not call the tool again.
Do not repeat the question.
"""
)

tools = [prometheus_tool]


# LLM
llm = OllamaLLM(model="llama3")


# Memory
memory = ConversationBufferMemory()


# Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    memory=memory,
    agent="zero-shot-react-description",
    verbose=True,
    max_iterations=1,
    early_stopping_method="generate",
    handle_parsing_errors=True
)

# Interactive loop
while True:

    question = input("\nAsk AI: ")

    response = agent.run(question)

    print("\nAnswer:\n", response)
