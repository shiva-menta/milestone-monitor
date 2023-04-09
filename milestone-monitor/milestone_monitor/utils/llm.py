import os

from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

load_dotenv()

BASE_LLM = OpenAI(temperature=0)
BASE_CHATBOT_LLM = ChatOpenAI(temperature=0)