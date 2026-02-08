from promptLlm import prompt_llm
from process_transcript import process_transcript

def prompt_tags(prompt):
	system_msg = "You are a text analysis assistant."
	llm_prompt = f"""
You will receive a user prompt as a single block of text.

Your task is to extract ONLY the most important keywords from the prompt.

Keywords may include:
- Main topics or concepts
- Names of people
- Organizations
- Locations
- Significant events
- Technical terms if relevant

Rules:
- Output ONLY keywords
- Separate keywords with commas
- Do NOT include explanations, numbering, or extra text
- Do NOT repeat similar keywords (this includes having both the abbreviated and unabbreviated versions of the keyword)
- Use concise, canonical names (e.g., "John F. Kennedy" not "JFK speech")
- For each keyword, also include any synonyms or closely related words you can think of, separated by commas. Include as many as you can come up with to improve accuracy.
- Any small part of the prompt which you can find a synonymous term for should have its synonym included.

Example Output:
Cold War, Cuban Missile Crisis, John F. Kennedy, Nikita Khrushchev, Cuba, United States, nuclear missiles, 1962

The goal is to find out which keywords specifically the user is searching for, which will then be used to match entries with
the user's desired search keywords.



Transcript:
<<<
{prompt}
>>>
"""
	
	response = prompt_llm(user_message=llm_prompt, system_message=system_msg)
	return response.split(', ')

def generate_tags(transcript):
	system_msg = "You are a text analysis assistant."
	llm_prompt = f"""
You will receive a transcript as a single block of text.

Your task is to extract ONLY the most important keywords from the transcript.

Keywords may include:
- Main topics or concepts
- Names of people
- Organizations
- Locations
- Significant events
- Technical terms if relevant

Rules:
- Output ONLY keywords
- Separate keywords with commas
- Do NOT include explanations, numbering, or extra text
- Do NOT repeat similar keywords (this includes having both the abbreviated and unabbreviated versions of the keyword)
- Use concise, canonical names (e.g., "John F. Kennedy" not "JFK speech")

Example Output:
Cold War, Cuban Missile Crisis, John F. Kennedy, Nikita Khrushchev, Cuba, United States, nuclear missiles, 1962

Transcript:
<<<
{transcript}
>>>
"""
	
	response = prompt_llm(user_message=llm_prompt, system_message=system_msg)
	return response.split(', ')
	
# for i in generate_tags(process_transcript('test_vid_transcript.txt')):
# 	print(i)

	

