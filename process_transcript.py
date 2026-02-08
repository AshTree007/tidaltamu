
def process_transcript(file_name) -> str:
	with open(file_name, 'r') as f:
		return f.readline()