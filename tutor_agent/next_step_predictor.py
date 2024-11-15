from mytiktoken import count_tokens
from tinydb import Query
import re
import time 
import random
import openai
import logging
from config import topics_table

# Create a logger for this file
logger = logging.getLogger(__name__)

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

def next_step_prediction_method(self):
    covered_topics = concatenate_with_spaces(self.covered_arr_to_set(self.topic.get('topics_covered',['0'])))
    prompt = f"""  
        This is the plan devised for the course: [begin] {self.plan} [end].
        This is the topics of the plan that has been covered so far [covered]: [begin] {covered_topics} [end]. (0 means nothing has been covered sofar)
        This is the last 10 messages of the conversation between the system and the user: [begin] {concatenate_with_spaces(self.messages_queue[-10:])} [end].

        Now you need to find out what should the system do next by refereing to to plan, [covered], and last 10 messages of the conversation using the following instructions:
            1- if the system need to start a new topic, extract that topic, example: start topic 1.1
            2- if the system need to continue the current topic, extract that, example: continue topic 1.1 
            3- if the user asked a question in the last message, the system need to answer that, extract that. example: answer user question 
            4- if the user asked a question and the system already answered but need to continue answer that, extract that: continue answering user question
            5- if the user asked for sth that is not covered in the first 4 instructions or
            if you encountered a situation that not covered in the first 4 instruction, predict the best next move, example: explaine sth more. (you should be as consice as possible) 
            6- it is very crucial that the system not repeat itself
        Then give me the extracted the system next move in this format and nothing else:
                "next_move":"<your extracted next move>",
      """
    max_retries = len(self.api_keys)+2
    retries = 0
    while retries <= max_retries:
        try:
            # Randomly select an API key for each call
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            parsed_response = openai.ChatCompletion.create(
                model = self.extraction_model,
                messages=[
                    {"role": "system", "content":prompt},
                ],
                temperature = 0,
                max_tokens = self.chat_max_tokens
            )
            content = parsed_response["choices"][0]["message"]["content"]
            return extract_next_move(self, content)
        except Exception as e:
            logger.error("Error in chat method: %s", str(e))
            retries += 1
            if retries <= max_retries:
                logger.info("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."

def extract_next_move(self, content):
    keys = ['next_move']
    parsed_values = {}
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    next_move = parsed_values.get("next_move", '')
    if next_move: 
        Topic_Query = Query()
        topic = topics_table.get(
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        
        # Get existing next_moves or initialize empty list
        current_moves = topic.get('next_moves', [])
        current_moves.append(next_move)
        
        # Update the document
        topics_table.update(
            {'next_moves': current_moves},
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        
        logger.info("Added next move: %s", next_move)
    
    return next_move