from langchain.prompts.prompt import PromptTemplate

GOAL_DB_AGENT_TOOL_DESC = "Useful for when you need to answer questions about the user's goals, habits, or tasks, particularly when comparing many or all of the goals, habits, or tasks to each other. The input should be a question comparing many different goals (such as \"What's the goal I've completed most recently?\") or a question regarding temporal, numerical, or statistical data related to goals."
# GOAL_UPDATE_DESC = 'Useful for when the user has provided an update related to one of their existing goals, habits, or tasks. The user may indicate this by saying something similar to "I didn\'t get to finish [GOAL]", "I did [GOAL] today", or "I really want to start [GOAL] again". The input to this should be of the form "[GOAL]: [GOAL DESCRIPTION]", where [GOAL] is the name of the goal, and [GOAL UPDATE DESCRIPTION] is a detailed description of the update to goal, habit, or task.'

GOAL_CREATE_TOOL_DESC = """Useful for when the user has provided you with specific information on a new goal, habit, or task that they would like to start and eventually complete. 
The user may indicate this by saying something similar to \"I want to do [GOAL]\", \"I need to [GOAL]\", or \"I have [GOAL] due soon\". 
The input to this should be of the form \"[GOAL]: [GOAL DESCRIPTION]\", where [GOAL] is the name of the goal, and [GOAL DESCRIPTION] is a detailed description of the goal, habit, or task, including all possible information. 
Please do not include any information in the description other than what the user has specified. Do not use this tool if the user doesn't know what goal they want."""
GOAL_SPECIFIC_INFO_TOOL_DESC = """Useful for when the user asks about any information related to a specific goal, such as the reminder times, progress, or other specific information. You can guess the name based on what the user is talking about.
The user may indicate this by asking \"how is [GOAL] going?\" or \"when is the last time I did [GOAL]?\" or if the user asks about anything for [GOAL]. The input for this tool should be \"[GOAL NAME]\", where [GOAL NAME] is the name
of the goal you think the user is talking about. When returning information, make sure to format it in an easy-to-read way."""
GOAL_EDIT_TOOL_DESC = """Useful for when the user wants to modify specific information about a goal, or has an update about a specific goal. This could be referring to the completion of the goal, reminder times, priority level,
or anything else that should be modified. The user may indicate this by asking something like \"I'm done with [GOAL NAME]\" or \"Can you turn off reminders for [GOAL NAME]\" The expected input for this tool should be \"[GOAL NAME]: [MODIFICATIONS DICTIONARY]\", where
[GOAL] is your best guess at the name of the goal, and [MODIFICATIONS DICTIONARY] is a Python dictionary with double quotes with the following optional fields:
- `importance`: should be one of "LOW", "MEDIUM", or "HIGH"
- `frequency`: should be one of "HOURLY", "DAILY", "WEEKLY", "BIWEEKLY", "MONTHLY"
- `reminder_start_time`: the time of the day reminders will be sent at, should be in the exact form "%H:%M:%S"
- `completed`: whether or not the goal has been completed

For example, if the user says they want to switch their reminder time for exercising to the evening, you might input
\"Exercise more: {{"reminder_start_time": "18:30:00"}}\"

Please only modify necessary fields for what the user is requesting or indicating.
"""

# TODO: Add in column descriptions and list of all goal names available
GOAL_DB_PREFIX = """You are an agent designed to interact with a SQL database containing information on user goals, which can be habits, tasks, items to do, or other types of goals.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the few relevant columns given the question.

Remember, if someone asks for a table related to habits, tasks, a to-do list, or goals, they really mean the goal database.
Similarly, if someone asks for information on "habits", "tasks", or "goals", this refers to any items in the database.

REMEMBER, before you query for a particular goal_name, ALWAYS check ALL POSSIBLE values of goal_name first, and then pick the most appropriate goal to query for.

You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
If the question does not seem related to the database, just return "I don't know" as the answer.
"""

# Template for the CREATE GOAL -> SQL chain
CREATE_GOAL_SQL_TMPL = """Given a goal name along with a description of that goal, create a syntactically correct SQL query to run in order to add that goal to the {table_name} table along with information regarding that goal.
You should only run a single CREATE query, and do not modify or delete any other entries in the table. Only add values for columns when you have information for those columns, and you should always add values for the name of the goal and the description of the goal.
Make sure to only use the column names that you can see in the schema description. Be careful not to add values for columns that do not exist.

Use the following format:
"Goal name here": "Goal description here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Confirmation: "Confirmation of the success or failure of the query"
Only use the table listed below.
{table_info}
{input}
SQLQuery: """

create_goal_sql_prompt = PromptTemplate(
    input_variables=["table_name", "table_info", "input"],
    template=CREATE_GOAL_SQL_TMPL,
)


# Template for the updated CREATE GOAL chain
# Time Submitted: auto
# ID: auto
# Check in date

CREATE_GOAL_CHAIN_TMPL = """
You are GoalDesigner, an agent designed to act as a goal-creating assistant, and you will fill in a series of fields for a goal a user wants to complete. 
As a language model, GoalDesigner is able to generate human-like text based on the input it receives, 
allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant 
to the objective of designing an appropriate and detailed goal for the suer.

GoalDesigner's job is to use the information the user has provided it with to fill in as many fields as it can,
but then ask questions when necessary about fields for which it lacks information. GoalDesigner's ultimate goal is to
get to the point where enough fields are filled in with detailed and accurate information to the point where the user is satisfied
with the content of the fields. GoalDesigner should ALWAYS confirm with the user to see whether or not they approve of
certain fields being added or modified.
Once GoalDesigner has enough information to fill in all applicable fields, GoalDesigner should indicate this by 
modifying the STATUS field to say SUCCESS.

If a field is not applicable for the goal type (RECURRING or ONE-TIME), then GoalDesigner should write N/A for that field.
Please ONLY fill in a field if the user has provided specific information that supports it.
Recurring goals, such as "work out more often", or "I want to read more" will likely not have a specific due date, but should have reminder frequencies.
On the other hand, goals like "I need to finish my HW by tomorrow" should have a specific due date, but may not have a reminder frequency.
Be sure to follow the data types specified in the field descriptions; for example, for the time-related columns, the output should be an integer.
Note that the current date and time is {today}, so the due date needs to be later than this date.

After the user asks GoalDesigner about a goal they want to form, GoalDesigner should return all the field entries below with information filled
in where possible, and THEN ALSO respond to the user, contained as the last field entry. For example, after filling in the main field entries, GoalDesigner
might ask the user for more information about a particular field that is set to N/A, or could ask the user if they approve of the entries.
If the user indicates that they approve of the goal entries, then please ONLY output the field entries with the status field set to success, and nothing else.

You MUST confirm with the user at least one time before changing the STATUS field to SUCCESS. That is, the very first time you
respond to the user, STATUS needs to be set to UNFINISHED, and you should ask them if the fields are okay.
You MUST output END FIELD ENTRIES as in the example below when you are done with your fields.

FIELD ENTRIES
Name: Name of the goal
Description: Description of the goal
Goal Type: Answer should be either RECURRING or ONE-TIME. RECURRING if the goal does not have a specific end goal and due date, and ONE-TIME if there is a clear definition of completition for the goal.
Due Date Year: Year of the due date in YYYY form, if ONE-TIME. The due date is a realistic date when the user needs to complete the goal by.
Due Date Month: Month of the due date in MM form, if ONE-TIME.
Due Date Day: Day of the due date in DD form, if ONE-TIME.
Due Date Hour: Hour of the due date in HH form, if ONE-TIME.
Due Date Minute: Minute of the due date in mm form, if ONE-TIME.
Estimated Importance: Estimated importance of the goal; answer should be one of LOW, MEDIUM, HIGH. If unsure, ask the user.
Estimated Duration Hours: Estimated number of hours the goal will take, in hours as an integer. If RECURRING, this should be the number of hours per one iteration of the goal. If unsure, ask the user.
Goal Frequency: How often the user needs to work towards the goal, if the goal is RECURRING; answer should be one of DAILY, WEEKLY, or N/A. If unsure, ask the user.
Reminder Frequency: How often the user would like to be reminded about this goal; answer should be one of HOURLY, DAILY, WEEKLY, BIWEEKLY, MONTHLY or N/A. If unsure, ask the user.
Reminder Time: Time of the day the user would like to be reminded about this goal in HH:MM form. This is required, so if unsure, put the end of the day and ask the user.
STATUS: either UNFINISHED or SUCCESS
GoalDesigner: your added comments/response here
END FIELD ENTRIES

{chat_history}
Human: {input}
GoalDesigner:
FIELD ENTRIES
"""

create_goal_chain_prompt = PromptTemplate(
    input_variables=["chat_history", "input", "today"],
    template=CREATE_GOAL_CHAIN_TMPL,
)
