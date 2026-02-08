from tags import prompt_tags
from database import search_files

def search(prompt):
	keywords = prompt_tags(prompt)
	matches = search_files(keywords)
	return matches

prompt = "I'm looking for an audio that mentioned electronics"
print("Results:")
for m in search(prompt):
	print(f"- {m['filename']}")

