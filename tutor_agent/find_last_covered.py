from config import topics_table, message_table, user_table
from mytiktoken import count_tokens
from tinydb import Query
import re
import time 
import random
import openai
import logging

# Create a logger for this file
logger = logging.getLogger(__name__)

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

def find_last_covered_method(self, content):
    covered_topics = concatenate_with_spaces(self.covered_arr_to_set(self.topic.get('topics_covered',['0'])))
    unique_values = set()
    for item in covered_topics:
        unique_values.update(item.split(','))
    covered_topics = sorted(unique_values)

    prompt = f""" Plan Tracking Prompt: 

    - Outline of Plan: [begin] {self.plan} [end].
    - Recently Covered Topics: [last_covered]: {covered_topics}.
    - Last 10 Messages: [begin] {concatenate_with_spaces(self.messages_queue[-10:])} [end].

    Task: Identify any plan topics covered in the last 10 messages not listed in [last_covered].

    Criteria for Covered Topics:
    1. Topic must be explicitly started by the system, including its number and name.
    2. Topic must be comprehensively covered and concluded.
    3. Topics should be covered sequentially. If a topic like 2.1 is discussed, but an intervening topic (like 1.5) has not been covered, 2.1 is not considered fully covered.
    4. Re-check for explicit mention and comprehensive coverage for precision.

    Output: 
    - If new topics are covered, format as: "covered":"<extracted topic numbers>".
    - If no new topics are covered, return: null.
    """
    #logger.debug("covered Prompt: %s", prompt)
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
            self.get_covered(content)
            return
        except Exception as e:
            logger.error("Error in chat method: %s", str(e))
            retries += 1
            if retries <= max_retries:
                logger.info("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."

def get_covered_method(self, content):
    keys = ['covered']
    parsed_values = {}
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    topics_covered = parsed_values.get("covered")
    logger.info("Covered now: %s", topics_covered)
    if topics_covered: 
        Topic_Query = Query()
        topic = topics_table.get(
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        
        # Get existing topics_covered or initialize empty list
        current_topics = topic.get('topics_covered', [])
        current_topics.append(topics_covered)
        
        # Update the document
        topics_table.update(
            {'topics_covered': current_topics},
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )

def covered_arr_to_set_method(self, covered):
    unique_topics = set()
    for entry in covered:
        # Extract the string of topics
        # Step 3: Split the string by comma to get individual topics
        topics = entry.split(',')
        # Step 4: Add each topic to the set
        unique_topics.update(topics)
    return sorted(list(unique_topics)) 
