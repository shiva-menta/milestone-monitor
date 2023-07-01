# Generates toolset and chatbot agent

from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain.memory import ConversationBufferWindowMemory

from utils.goal_prompts import (
    GOAL_CREATE_TOOL_DESC,
    GOAL_SPECIFIC_INFO_TOOL_DESC,
    GOAL_EDIT_TOOL_DESC,
)
from utils.goal_tools import (
    init_conversational_create_goal_tool,
    init_get_specific_goal_tool,
    init_modify_specific_goal_tool,
)
from utils.llm import BASE_CHATBOT_LLM

# MAIN_CHATBOT_PREFIX = """
# You are a conversational bot that specializes in setting goals for users and giving them recommendations.
# If you haven't already, you should make sure to let the user know that they should provide you with goals, habits,
# or other tasks they wish to work on and can be general or specific as they want about what they're looking for.
# """


# Generates the tools for a specific user
def generate_main_tools(user: str):
    tools = [
        Tool(
            name="Create Goal",
            func=init_conversational_create_goal_tool(user),
            description=GOAL_CREATE_TOOL_DESC,
            return_direct=True,
        ),
        Tool(
            name="Get Specific Goal Info",
            func=init_get_specific_goal_tool(user),
            description=GOAL_SPECIFIC_INFO_TOOL_DESC,
        ),
        Tool(
            name="Modify Specific Goal Info",
            func=init_modify_specific_goal_tool(user),
            description=GOAL_EDIT_TOOL_DESC,
        ),
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

    # HACK:
    def _handle_error(error) -> str:
        print(error)
        return str(error)

    # Initialize agent
    print()
    agent_chain = initialize_agent(
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        tools=generate_main_tools(user),
        llm=BASE_CHATBOT_LLM,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors=_handle_error,
        # agent_kwargs={"prefix": MAIN_CHATBOT_PREFIX},
    )
    print("PROMPT TEMPLATE:", agent_chain.agent.llm_chain.prompt)

    # Call the agent using agent.run(input="...")
    return agent_chain
