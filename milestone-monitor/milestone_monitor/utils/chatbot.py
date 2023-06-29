# Generates toolset and chatbot agent

from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain.memory import ConversationBufferWindowMemory

from utils.goal_prompts import GOAL_DB_AGENT_TOOL_DESC, GOAL_CREATE_TOOL_DESC
from utils.goal_tools import get_conversational_create_goal_tool
from utils.llm import BASE_CHATBOT_LLM

# MAIN_CHATBOT_PREFIX = """
# You are a conversational bot that specializes in setting goals for users and giving them recommendations.
# If you haven't already, you should make sure to let the user know that they should provide you with goals, habits,
# or other tasks they wish to work on and can be general or specific as they want about what they're looking for.
# """


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
def get_main_chatbot(
    user: str, memory: ConversationBufferWindowMemory, DEBUG=False
) -> AgentExecutor:
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
        agent="conversational-react-description",
        tools=generate_main_tools(user),
        llm=BASE_CHATBOT_LLM,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors="Check your output and make sure it conforms!",
        # agent_kwargs={"prefix": MAIN_CHATBOT_PREFIX},
    )
    print("PROMPT TEMPLATE:", agent_chain.agent.llm_chain.prompt.template)

    # Call the agent using agent.run(input="...")
    return agent_chain
