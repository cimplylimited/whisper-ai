from openai import OpenAI
import os
import json
import datetime

# The purpose of this script is to take a transcription and to build an article summary.
# This version makes a small change which asks AI to write in the 1st person.

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set the OpenAI API key from the environment variable

# Define a function to get model completion
def get_completion(prompt, model="o1-preview"):
    messages = [{"role": "system", "content": prompt}]
    response = client.chat.completions.create(model=model,
    messages=messages,
    temperature=0.3)
    return response.choices[0].message.content

# Input variables
contents = [
f"""
Podcast Next Steps: Mark/Anthony/Steve - 2024/11/25 09:58 EST - Transcript

Attendees

Transcript




"""
]

prompt = f"""Please review the content from a meeting transcript.  Your task will be to create an output file that our team can use to review and plan for the future.  It should be comprehensive:  
 - First, take extra time to review the whole transcript and organize the main ideas. 
 - Then review your analysis to extract key takeaways and next steps,
 - Then review the analysis against the transcript to see if anything important is missing,
 - Then create an outline of the content topics major headlines,
 - Then bullet out important points for the outline headings,
 - Then write a summary that is comprehensive and detailed
 - Then create a Title for the summary based on the title of the meeting itself in the transcript with attendees and a date/time of the meeting,
 - Then put together Next Steps and To Dos and assign them to an owner
 - Then ideate on key current and future strategic initiatives to focus on and organize them according to topics

 \n"""

for index, content in enumerate(contents, start=1):
    prompt += f"{index}. Content: {content}\n"

# Define the instruction for the model

instruction = f"""

Your goal is to make a comprehensive summary of a meeting, organize the meeting key points into an outline, 
showcase key next steps, and highlight any thought starters for strategic initiatives and priorities.

Make sure your bullets are detailed.

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
