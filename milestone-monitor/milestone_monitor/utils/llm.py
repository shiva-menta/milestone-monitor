import os

from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

load_dotenv(override=True)

BASE_LLM = OpenAI(temperature=0)
# BASE_CHATBOT_LLM = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0301")
BASE_CHATBOT_LLM = ChatOpenAI(temperature=0, model="gpt-4")
