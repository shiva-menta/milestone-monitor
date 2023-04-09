from langchain.agents import AgentExecutor, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from utils.goal_prompts import GOAL_DB_AGENT_TOOL_DESC, GOAL_CREATE_TOOL_DESC
from utils.goal_tools import conversational_create_goal_tool
from utils.llm import BASE_CHATBOT_LLM


default_tools = [
    # Tool(
    #     name="Goal Database Agent",
    #     func=XXX
    #     description=GOAL_DB_AGENT_TOOL_DESC
    # ),
    Tool(
        name="Create Goal",
        func=conversational_create_goal_tool,
        description=GOAL_CREATE_TOOL_DESC
    )
]


# Retrieves a chatbot for a particular user
def get_chatbot(user: str, DEBUG=False) -> AgentExecutor:

    # Create new memory (change in the future to retrieve memory for a specific user)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Initialize agent
    agent_chain = initialize_agent(
        default_tools, 
        BASE_CHATBOT_LLM,
        agent="chat-conversational-react-description", 
        verbose=DEBUG, 
        memory=memory
    )

    # Call the agent using agent.run(input="...")
    return agent_chain