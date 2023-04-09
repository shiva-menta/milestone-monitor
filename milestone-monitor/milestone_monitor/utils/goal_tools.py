import os
import sys
import json

from datetime import datetime
from re import sub

from langchain import OpenAI, LLMChain
from langchain.agents import tool, create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.memory import ConversationBufferWindowMemory

from utils.embeddings import create_embedding
from utils.goal_prompts import GOAL_DB_PREFIX, create_goal_chain_prompt
from utils.interactions import create_goal
from utils.llm import BASE_LLM

##
# Conversational create goal tool
##

goal_create_memory = ConversationBufferWindowMemory(
    k=2, 
    memory_key="history",
    input_key="input", 
    ai_prefix="AI", 
    human_prefix="User"
)

create_goal_chain = LLMChain(
    llm=BASE_LLM,
    prompt=create_goal_chain_prompt, 
    verbose=True, 
    memory=goal_create_memory,
)

# Helper function to convert a string to camel case
def camel_case(s):
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].lower(), s[1:]])

# Helper function to parse the field entries as text to a dict
def parse_field_entries(field_entries: str):
    return {field[0]: field[1] for field in [field.split(": ") for field in field_entries.split('\n')]}

# Helper function to convert the given text fields dict to JSON
def text_fields_to_json(fields: dict):
    fields = fields.copy()
    fields['Due Date'] = datetime(
        int(fields["Due Date Year"]),
        int(fields["Due Date Month"]),
        int(fields["Due Date Day"]),
        int(fields["Due Date Hour"]),
        int(fields["Due Date Minute"])
    )
    fields['Is Recurring'] = (int) (fields["Goal Type"] == "RECURRING")

    for key in ["Due Date Year", "Due Date Month", "Due Date Day", "Due Date Hour", "Due Date Minute", "Goal Type"]:
        del fields[key]

    return json.dumps({camel_case(key): value if value != 'N/A' else None for key, value in fields.items()}, default=str)

# TODO: take SMS input
@tool
def conversational_create_goal_tool(query: str) -> str:
    '''
    A tool which may prompt for additional user input to aid for the creation of a user goal.
    '''
    user_input = query
    current_field_entries = None

    # SET CURRENT CONVO TYPE TO CREATE GOAL


    # QUERY CREATE GOAL MODEL

    while True:
        current_full_output = create_goal_chain.predict(input=user_input, today=datetime.now())

        current_field_entries = parse_field_entries(current_full_output.split('END FIELD ENTRIES')[0].strip())
        current_conversational_output = current_full_output.split('END FIELD ENTRIES')[1].strip()

        print(current_field_entries)

        if current_field_entries["STATUS"] == "SUCCESS":
            break

        print(f"Temp field entries: {current_field_entries}")
        print(f"Model: {current_conversational_output}")

        user_input = input("User: ")

    # Parse current field entries here
    # and add them to the database
    fields_json = text_fields_to_json(current_field_entries)
    goal_name_embedding = create_embedding(current_field_entries["name"])
    create_goal(fields_json)

    return f"The goal data being added is as follows:\n{current_field_entries}\nGoal added successfully!"


##
# Goal database reader tool
##

@tool
def specific_goal_info_tool(query: str) -> str:
    '''
    A tool used to retrieve info about a specific goal.
    '''
    query_embedding = create_embedding(query)
    return "Info"


# goal_db_toolkit = SQLDatabaseToolkit(db=goal_database)
# goal_db_agent_executor = create_sql_agent(
#     llm=OpenAI(temperature=0),
#     toolkit=goal_db_toolkit,
#     prefix=GOAL_DB_PREFIX,
#     verbose=True,
# )
# goal_db_reader_tool = goal_db_agent_executor.run

# @tool
# def goal_db_reader_