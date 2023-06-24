# Generates toolset and chatbot agent

from langchain import OpenAI, LLMChain
from langchain.agents import AgentExecutor, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory

from utils.goal_prompts import GOAL_DB_AGENT_TOOL_DESC, GOAL_CREATE_TOOL_DESC
from utils.goal_tools import get_conversational_create_goal_tool
from utils.llm import BASE_CHATBOT_LLM
from utils.msg_hist import get_user_hist


# Generates the tools for a specific user
def generate_main_tools(user: str):
    tools = [
        # Tool(
        #     name="Goal Database Agent",
        #     func=XXX
        #     description=GOAL_DB_AGENT_TOOL_DESC
        # ),
        Tool(
            name="Create Goal",
            func=get_conversational_create_goal_tool(user),
            description=GOAL_CREATE_TOOL_DESC,
            return_direct=True,
        )
    ]

    return tools


# Retrieves the main chatbot for a particular user (equips it with memory)
def get_main_chatbot(user: str, memory: ConversationBufferWindowMemory, DEBUG=False) -> AgentExecutor:

    # Create new memory if doesn't exist yet
    # if memory is None:
    #     memory = ConversationBufferWindowMemory(
    #         memory_key="chat_history",
    #         input_key="input",
    #         return_messages=True, 
    #         k=3
    #     )
    assert memory is not None

    # Initialize agent
    agent_chain = initialize_agent(
        generate_main_tools(user), 
        BASE_CHATBOT_LLM,
        agent="chat-conversational-react-description", 
        verbose=DEBUG, 
        memory=memory
    )

    # Call the agent using agent.run(input="...")
    return agent_chain

