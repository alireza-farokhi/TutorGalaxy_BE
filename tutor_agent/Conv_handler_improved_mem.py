import openai
import time
import random
import asyncio
from config import *
import tiktoken
import os
from dotenv import load_dotenv
import time
from mytiktoken import count_tokens
from math import floor
from .process_message import process_message_method, process_with_buffer_method
from .extract_plan_learning_style import extract_plan_learning_style_method, analyse_content_method
from .process_message_with_plan import process_message_with_plan_method, process_with_plan_method
from .preference_checker import preference_check_method, get_prefer_method
from .find_last_covered import find_last_covered_method, get_covered_method, covered_arr_to_set_method 
from .next_step_predictor import next_step_prediction_method
from .plan_checker import plan_checker_method, plan_check_method, add_plan_to_topic_method 
from .process_message_with_temp_plan import process_message_with_temp_plan_method, process_with_temp_plan_method 
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime
import pytz
from tinydb import Query



deserializer = TypeDeserializer()
     

math_prompt = r"""Here's how you should format mathematical formulas according to the instruction provided:
1. For inline mathematical expressions (those that appear within a line of text), you should enclose the expression in a single dollar sign on each side. For example:
   - The formula for the area of a circle with radius $r$ is given by $A = \pi r^2$.
2. For displayed mathematical expressions (those that are centered and on their own line), you should enclose the expression in double dollar signs or use the LaTeX display math environment and square brackets. For example:
- The quadratic formula is given by:
     $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$
Here's how the provided examples should be formatted:
- The central equation is the Einstein Field Equation:
  $$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu}$$
  Where:
  - $G_{\mu\nu}$ is the Einstein tensor, representing the curvature of spacetime. $\Lambda$ is the cosmological constant. 
  """




def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

class TeachingAssistant_stream:
    
    ## Methods Init
    process_message = process_message_method
    process_with_buffer = process_with_buffer_method
    extract_plan_learning_style = extract_plan_learning_style_method
    analyse_content = analyse_content_method
    process_message_with_plan = process_message_with_plan_method
    preference_check = preference_check_method
    process_with_plan =  process_with_plan_method 
    find_last_covered = find_last_covered_method
    get_covered = get_covered_method
    next_step_prediction = next_step_prediction_method
    get_prefer = get_prefer_method
    covered_arr_to_set = covered_arr_to_set_method
    plan_checker = plan_checker_method
    plan_check = plan_check_method
    add_plan_to_topic = add_plan_to_topic_method
    process_message_with_temp_plan = process_message_with_temp_plan_method
    process_with_temp_plan = process_with_temp_plan_method

    
    def __init__(self, api_keys, conversation_model="gpt-4", extraction_model="gpt-4" , temperature=0.7, max_tokens=5000):
        self.api_keys = api_keys
        self.model_engine = conversation_model
        self.conversation_model = conversation_model
        self.extraction_model = extraction_model 
        self.summerizer_model_engine = conversation_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.state = 0
        self.user_messages = []
        self.system_messages = []
        self.summary = None 
        self.messages_queue = []
        self.mq_len = 15
        self.discussion = None
        self.conversation_history = []
        self.chat_start_prompt = None
        self.chat_continue_prompt = None
        self.gpt_max_tokens = 8000
        self.chat_starter_max_tokens = 1000
        self.chat_max_tokens = 1500
        self.guard_tokens = 500
        self.max_summarizer_words = 2000
        self.max_token_allowed = self.gpt_max_tokens - self.chat_max_tokens - self.guard_tokens
        self.default_summary = """Summarize the conversation between 'system' and 'user'. This is the conversation: {}. 
The order of the of the conversation should remain intact. 
In your summary it should be very clear what 'system' said and what 'user' said in order. 
keep the whole summary less than {} words. 
If the text cotain the name of the 'system' or the 'user', remember to bring it in the summary intact. 
Your summay should maintain the course of conversation. Specially when the conversation took a turn.
if the system put out a plan for the conversation, bring the plan with all the details in the summary, I mean copy and paste level of details, everything, intact. The plan may get revised throgh the conversation
put the latest version with all the details in your summary.
User preferences is very important, if user express any prefernce bring put it in your summary. """
        self.buffer = []
        self.plan_done = False
        self.execution_done = False
        self.sequential_prompting = False




    
    def chatstarter(self, prompt):
            max_retries = 2
            retries = 0

            while retries <= max_retries:
                try:
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.conversation_model,
                        messages=[
                            {"role": "system", "content": f"{self.chat_start_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = self.temperature,
                        max_tokens = self.chat_starter_max_tokens,
                        stream = True
                    )
                    for line in parsed_response:
                        if 'content' in line['choices'][0]['delta']:
                            yield line['choices'][0]['delta']['content']
                    return
                except Exception as e:
                    print(f"Error in chat method: {e}")
                    retries += 1
                    if retries <= max_retries:
                        print("Retrying with a new API key...")
                        time.sleep(1)
                    else:
                        return "Sorry, there was an issue connecting to the API. Please try again later."
    
    
    def chat(self, prompt):
        max_retries = len(self.api_keys) + 2
        retries = 0
        while retries <= max_retries:
            try:
                
                openai.api_key = self.api_keys[retries % len(self.api_keys)]
                parsed_response = openai.ChatCompletion.create(
                    model = self.conversation_model,
                    messages=[
                        {"role": "system", "content": f"""This is the record of the conversation that you have had with the user so far:[begin]{self.discussion}[end]. 
                        You are the system. So you continue disscusion as the system. You are the system so should never answer like this 'user = ...' . {self.chat_continue_prompt}. {math_prompt}"""},
                        {"role": "user", "content": f"{prompt}"},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.chat_max_tokens,
                    stream = True
                )
                for line in parsed_response:
                    if 'content' in line['choices'][0]['delta']:
                        yield line['choices'][0]['delta']['content']
                return
            except Exception as e:
                print(f"Error in chat method: {e}")
                retries += 1
                if retries <= max_retries:
                    print("Retrying with a new API key...")
                    time.sleep(1)
                else:
                    return "Sorry, there was an issue connecting to the API. Please try again later."
                    
    def summarizer(self, prompt):
        max_retries = 3
        retries = 0
        prompt_tokens = count_tokens(prompt)
        prompt_words = floor(prompt_tokens*0.75)
        summary_words = max(floor(prompt_words/4), self.max_summarizer_words)
        while retries <= max_retries:
            try:
                # Randomly select an API key for each call
                openai.api_key = self.api_keys[retries % len(self.api_keys)]
                parsed_response = openai.ChatCompletion.create(
                    model = self.extraction_model,
                    messages=[
                        {"role": "system", "content":self.summarizer_prompt.format(prompt, summary_words)},
                    ],
                    temperature = 0,
                    max_tokens = floor(summary_words/0.6)
                )
                content = parsed_response["choices"][0]["message"]["content"]
                return content
            except Exception as e:
                print(f"Error in chat method: {e}")
                retries += 1
                if retries <= max_retries:
                    print("Retrying with a new API key...")
                    time.sleep(1)
                else:
                    return "Sorry, there was an issue connecting to the API. Please try again later."


    def handle_message(self, user_input: str, user_email, topic_id):
        self.user_email, self.topic_id = user_email, topic_id
        self.get_user_and_topic()

        if 'plan' not in self.topic and 'tempplan' not in self.topic:
            if self.plan_checker(user_input):
                self.add_plan_to_topic()
                self.topic['tempplan'] = True

        if 'plan' not in self.topic and 'tempplan' not in self.topic:
            for chunk in self.process_message(user_input):
                yield chunk
        elif 'tempplan' in self.topic and 'plan' not in self.topic:
            for chunk in self.process_message_with_temp_plan(user_input):
                yield chunk
        else:
            for chunk in self.process_message_with_plan(user_input):
                yield chunk 




    def get_user_and_topic(self):
        Topic_Query = Query()
        self.topic = topics_table.get(
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        if not self.topic:
            return "Topic not found" 
        
        self.chat_start_prompt = self.topic['chatstarter']
        self.tutor_behaviour = str(self.topic.get('tutor_bahaviour', "1"))
        ## handling sequential prompting
        print("tutor behaviour:", self.tutor_behaviour)
        if self.tutor_behaviour == "1":  
            if 'chat' in self.topic:
                self.chat_continue_prompt = self.topic['chat']
            else:
                self.sequential_prompting = True
                if not self.topic['Planning_done'] and not self.topic['Excecution_done']:
                    self.chat_continue_prompt = self.topic['Planning_prompt']
                if self.topic['Planning_done'] and not self.topic['Excecution_done']:
                    self.chat_continue_prompt = self.topic['Excecution_prompt']
                if self.topic['Planning_done'] and self.topic['Excecution_done']:
                    self.chat_continue_prompt = self.topic['Post_Excecution_prompt']
        else:
            self.chat_continue_prompt = f"""{self.topic['who_you_are']}.
             your persona: {self.topic['persona_pref']}. You role is to answer user's question."""

        self.chat_continue_prompt_token_number = count_tokens(self.chat_continue_prompt)
        self.state = self.topic['state']
        self.summary = self.topic['summary']
        self.messages_queue_ids = self.topic['messages_queue']
        self.summarizer_prompt = self.topic.get('summarizer_prompt', self.default_summary)
        self.create_messages_queue()
        return 
    
    def create_messages_queue(self):
        Message_Query = Query()
        self.messages_queue = []
        
        # Get messages in order of the queue
        for message_id in self.messages_queue_ids:
            message = message_table.get(
                (Message_Query.topics_id == self.topic_id) & 
                (Message_Query.message_id == message_id)
            )
            if message:
                self.messages_queue.append(message['message'])
    
    def create_message_in_db_and_update_state(self, message):
        new_message_id = str(int(time.time()))
        #time 
        pst = pytz.timezone('America/Los_Angeles')
        current_time_pst = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create new message
        new_message = {
            'topics_id': self.topic_id,
            'message_id': new_message_id,
            'message': message,
            'timestamp': current_time_pst,  
        }
        message_table.insert(new_message)
        
        # Update topic
        Topic_Query = Query()
        topic = topics_table.get(
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        
        if topic:
            messages = topic.get('messages', []) + [new_message_id]
            messages_queue = topic.get('messages_queue', []) + [new_message_id]
            
            topics_table.update({
                'messages': messages,
                'messages_queue': messages_queue,
                'Planning_done': self.plan_done,
                'Excecution_done': self.execution_done,
                'state': self.state
            }, (Topic_Query.userId == self.user_email) & 
                (Topic_Query.topics_id == self.topic_id))
    
    def update_summary_and_messages_queue(self):
        Topic_Query = Query()
        topic = topics_table.get(
            (Topic_Query.userId == self.user_email) & 
            (Topic_Query.topics_id == self.topic_id)
        )
        
        if topic:
            current_messages_queue = topic['messages_queue']
            updated_messages_queue = current_messages_queue[self.len_purge_queue:]
            
            topics_table.update({
                'messages_queue': updated_messages_queue,
                'summary': self.summary
            }, (Topic_Query.userId == self.user_email) & 
                (Topic_Query.topics_id == self.topic_id))




        

    
    

