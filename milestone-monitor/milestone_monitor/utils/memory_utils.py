from typing import List

from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import messages_from_dict, messages_to_dict

def dict_to_memory(memory_dict: List[dict], k=3) -> ConversationBufferWindowMemory:
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        ai_prefix="AI", 
        human_prefix="User",
        input_key="input",
        return_messages=True, 
        k=k,
    )

    buffer = messages_from_dict(memory_dict)
    for human, ai in zip(buffer[0::2], buffer[1::2]):
        memory.save_context({"input": human.content}, {"output": ai.content})

    return memory

def memory_to_dict(memory: ConversationBufferWindowMemory) -> List[dict]:
    return messages_to_dict(memory.buffer)

def create_main_memory(k=3)-> ConversationBufferWindowMemory:
    return ConversationBufferWindowMemory(
        memory_key="chat_history",
        ai_prefix="AI", 
        human_prefix="User",
        input_key="input",
        return_messages=True, 
        k=k,
    )