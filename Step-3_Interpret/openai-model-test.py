from openai import OpenAI
import os, json

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
models = client.models.list()
print([m.id for m in models.data][:20])   # list first 20 model IDs you can actually call