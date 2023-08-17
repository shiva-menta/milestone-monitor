# Generates toolset and chatbot agent

from datetime import datetime

from langchain.tools import Tool
from langchain.agents import AgentExecutor, AgentType, initialize_agent
from langchain.memory import ConversationBufferWindowMemory

from textwrap import dedent

from utils.goal_prompts import (
    GOAL_SPECIFIC_INFO_TOOL_DESC,
    GOAL_ALL_INFO_TOOL_DESC,
    GOAL_EDIT_TOOL_DESC,
    GOAL_CREATE_TOOL_DESC_ALT,
    GOAL_CREATE_TOOL_EDIT_DESC_ALT,
    GOAL_CREATE_FINISH_TOOL_DESC,
)
from utils.goal_tools import (
    init_get_specific_goal_tool,
    init_get_all_goals_tool,
    init_modify_specific_goal_tool,
    init_create_goal_tool_ALT,
    init_create_goal_modify_tool_ALT,
    init_create_goal_finish_tool_ALT,
)
from utils.redis_user_data import get_user_hist
from utils.llm import BASE_CHATBOT_LLM


MILESTONE_MONITOR_PREFIX = """
Milestone Monitor is a very friendly large language model designed to help users with pursuing their personal habits and goals.

Milestone Monitor is capable of assisting the user with a wide range of tasks, related to keeping track of personal goals and providing helpful advice. As a language model, Milestone Monitor is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Milestone Monitor is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of goal-related questions. Additionally, Milestone Monitor is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on any topic related to managing goals.

If the user indicates that they are interested in starting a goal, accomplishing something, or any kind of personal improvement, Milestone Monitor should use the appropriate tools to help the user accomplish that.

Overall, Milestone Monitor is a powerful but friendly system that can help with a wide range of goal-related tasks and provide valuable insights and information on any topic for the purpose of forming personal goals. Whether you want to start a specific new goal or just want to have a conversation about getting better at your personal goals, Milestone Monitor is here to help.

{extra_notes}

Note that the current time is {current_time}.
"""


# Generates all tools needed by LangChain for a specific user.
# "dont_finish_create" is a hacky workaround for the fact that
# langchain doesn't allow you to dynamically decide whether or not
# to return outputs directly
def generate_main_tools(user: str, dont_finish_create: bool):
    print(dont_finish_create)

    tools = [
        Tool.from_function(
            name="Start Create New Goal",
            func=init_create_goal_tool_ALT(user),
            description=GOAL_CREATE_TOOL_DESC_ALT,
            return_direct=True,
        ),
        Tool.from_function(
            name="Modify New Unsaved Goal",
            func=init_create_goal_modify_tool_ALT(user),
            description=GOAL_CREATE_TOOL_EDIT_DESC_ALT,
            return_direct=True,
        ),
        Tool.from_function(
            name="Finish Creating New Goal",
            func=init_create_goal_finish_tool_ALT(user),
            description=str(GOAL_CREATE_FINISH_TOOL_DESC),
            return_direct=bool(dont_finish_create),
        ),
        Tool.from_function(
            name="Get Specific Existing Goal Info",
            func=init_get_specific_goal_tool(user),
            description=GOAL_SPECIFIC_INFO_TOOL_DESC,
        ),
        Tool.from_function(
            name="Get All Goals List",
            func=init_get_all_goals_tool(user),
            description=GOAL_ALL_INFO_TOOL_DESC,
        ),
        Tool.from_function(
            name="Modify Specific Existing Goal Info",
            func=init_modify_specific_goal_tool(user),
            description=GOAL_EDIT_TOOL_DESC,
        ),
    ]

    return tools


# Retrieves the main chatbot for a particular user (equips it with memory)
def get_main_chatbot(
    user: str,
    memory: ConversationBufferWindowMemory,
    is_creating_goal: bool,
    is_responding_to_queue=False,
    dont_finish_create=False,
    DEBUG=False,
) -> AgentExecutor:
    assert memory is not None
    user_data = get_user_hist(user)

    # HACK:
    def _handle_error(error) -> str:
        print(error)
        return str(error)

    # If the user is in the middle of
    create_goal_note = ""
    if is_creating_goal:
        create_goal_note = "IMPORTANT: Please note, the user is currently in the process of creating a goal, which has not yet been added to the database. If the user expresses approval at the previous iteration of the goal data, you MUST use the appropriate tool to finish the process of goal creation and add it to the database. You should NOT create any other new goals during this process."

    queue_note = ""
    if is_responding_to_queue:
        queue_note = dedent(
            f"""\nIMPORTANT: Please note that the last message from the user was sent BEFORE the final response(s) from Milestone Monitor that you can see here. The last response you can see here from Milestone Monitor was being written while the user was also texting the chatbot. In other words, the user is responding to the second-to-last message Milestone Monitor sent, and could not have seen the final message Milestone Monitor sent here, so please respond appropriately. For example, if Milestone Monitor just responded with information for a new goal, and the user appears to have responded \"ok\", the user is not responding to that new information, but to an older chatbot message. Please DO NOT repeat any prior actions you just took, such as creating a new goal."""
        )

    # Initialize agent
    # TODO: need datetime to provide the actual local time
    agent_chain = initialize_agent(
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        tools=generate_main_tools(
            user,
            user_data["last_user_message_time"]
            and user_data["current_field_entries_last_modified"]
            and datetime.strptime(
                user_data["last_user_message_time"], "%m/%d/%Y %H:%M:%S"
            )
            < datetime.strptime(
                user_data["current_field_entries_last_modified"], "%m/%d/%Y %H:%M:%S"
            ),
        ),
        llm=BASE_CHATBOT_LLM,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors=_handle_error,
        agent_kwargs={
            "system_message": MILESTONE_MONITOR_PREFIX.format(
                current_time=datetime.strftime(datetime.now(), "%m/%d/%Y %H:%M:%S"),
                extra_notes=create_goal_note + queue_note,
            )
        },
    )
    # print(
    #     "PROMPT TEMPLATE:",
    #     agent_chain.agent.llm_chain.prompt.messages[0].prompt.template,
    # )
    # print(len(agent_chain.agent.llm_chain.prompt.messages))

    # Call the agent using agent.run(input="...")
    return agent_chain
