from openai import OpenAI
import os
import json
import datetime

# The purpose of this script is to take a transcription and to build an article summary.
# This version makes a small change which asks AI to write in the 1st person.

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set the OpenAI API key from the environment variable

# Define a function to get model completion
def get_completion(prompt, model="gpt-4-0125-preview"):
    messages = [{"role": "system", "content": prompt}]
    response = client.chat.completions.create(model=model,
    messages=messages,
    temperature=0.5)
    return response.choices[0].message.content

# Input variables
contents = [
f"""


"""
]

prompt = f"""Please review the content from a meeting transcript and think about the best way to summarize and comment on this discussion.  
First, take extra time to review the whole transcript and organize the main ideas. Then you will create an article summarizing the key points and implications 
in an editorial format in the tone of a scientific magazine.  You are to write this article in the 1st person as LexDAO.  Lexdao is a guild of legal
engineers focused on Law as a Public Good.  You should write this as if you are speaking to 
people who were both at the event and who might have not attended but want to get a feel for 
what was discussed.  LexDAO hosted this event with MetaCartel and Unlock Protocol.  
After you write your summary, please outline key points made and outline any tangible next steps:\n"""

for index, content in enumerate(contents, start=1):
    prompt += f"{index}. Content: {content}\n"

# Define the instruction for the model

instruction = f"""

Your goal is to read the transcript and create an article that talks about this session.  The Panel was a group of people at 
a live event with an audience.  Your summary must be between 1500 and 2000 words and
be structured as an editorial piece.  Write it in an interesting way that is readable and professional.  Please also 
include a section that shows the presenters names and email address only if you have them explicitly from the transcript.

When you are finished creating the summary, you must create a well-structured JSON response with a consistent format.   
Please do not let response variables show up more than once, make sure to use '\\n' for 
each new line, and make sure the json output is perfectly structured before returning it:

{prompt}"""  # Double curly braces to escape literal curly braces

# Get the response from the model
response = get_completion(instruction, model="gpt-4-1106-preview")

# Replace '\n' with actual newlines in the JSON content
response_with_newlines = response.replace('\\n', '\n')

# Manually format the response to ensure the desired structure
formatted_response = f'{{\n    "response": {response_with_newlines}\n}}'

# Prompt for the desired filename
output_filename = input("Enter the filename for the JSON output (e.g., quotes_output.json): ")

# Define the path to save the JSON file
file_path = os.path.join(os.getcwd(), output_filename)

# Save the response as a JSON file
with open(file_path, "w") as json_file:
    json_file.write(formatted_response)

print(f"Response has been saved to '{output_filename}' in the current directory.")
