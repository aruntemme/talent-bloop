import os
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import TextLoader
from dotenv import dotenv_values

env_vars = dotenv_values('.env')

loader = TextLoader('profile.txt')

os.environ["OPENAI_API_KEY"] = env_vars["OPENAI_KEY"]

def get_user(query):
    chatgpt = ChatOpenAI(model_name='gpt-3.5-turbo')
    gpt3 = OpenAI(model_name='text-davinci-003')
    from langchain.indexes import VectorstoreIndexCreator

    # persist index with loader db create persist db
    index = VectorstoreIndexCreator().from_loaders([loader])

    return index.query(query)