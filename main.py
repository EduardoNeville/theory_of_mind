from dataclasses import dataclass
import os
import openai
import random
import time
import csv

#
# Configurations
#

# Number of questions to randomly select and send to GPT
NUMBER_OF_QUESTIONS = 100

# Sleep time
# In case you are throttled with GPT4 for example, increase this wait between requests
SLEEP_TIME = 0

# GPT Model to use
OPEN_AI_MODEL = "gpt-4"

# OPEN AI API setup based on API Key and ORG ID
# These are set in env variables - on Replit they are in secrets
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")


@dataclass
class Question:
  question_type: str
  story_type: str
  actions: tuple
  question: str
  answer: str


def main():

  # Load question descriptions
  descriptions = []

  with open('data/test.trace', 'r') as description_file:
    for line in description_file:

      line = line.strip()
      classifications = line.split(",")

      question_type = classifications[-2]
      story_type = classifications[-1]

      descriptions.append((question_type, story_type))

  actions_questions_answers = []

  # Load actions and questions
  with open('data/test.txt', 'r') as questions_file:

    actions = []

    for line in questions_file:
      line = line.strip()

      # This is the quetion and end of this sceanrio
      if "?" in line:

        # Get question and answer
        question_and_answer = line.split("?")
        question = question_and_answer[0] + "?"
        answer = question_and_answer[1].strip().replace("\t",
                                                        " ").split(" ")[0]

        actions_questions_answers.append((tuple(actions), question, answer))

        actions = []

      else:
        actions.append(line)

  # Combine into questions list
  questions = []

  for i in range(len(descriptions)):

    question_type, story_type = descriptions[i]
    actions, question, answer = actions_questions_answers[i]

    questions.append(
      Question(question_type, story_type, actions, question, answer))

  # Randomly select questions
  # Send to GPT to answer
  # Save results to CSV
  visited_index = set()
  time_string = time.strftime("%Y-%m-%d %H:%M:%S")
  csv_filename = "results-" + OPEN_AI_MODEL + '-' + time_string + ".csv"
  csvfile = open(csv_filename, 'a')
  csv_writer = csv.writer(csvfile)
  csv_writer.writerow([
    "actions", "question", "answer", "question_type", "story_type",
    "gpt_prompt", "gpt_response", "gpt_answer"
  ])

  for i in range(NUMBER_OF_QUESTIONS):
    print("Selecting Question:", i + 1, "of", NUMBER_OF_QUESTIONS)

    r = random.choice(list(range(len(descriptions))))

    while r in visited_index:
      r = random.choice(list(range(len(descriptions))))

    visited_index.add(r)

    print("Chose Random Index:", r)

    question = questions[r]
    action_list = '\n'.join(question.actions)

    message_content = f"""You are a highly analytical, detail-oriented assistant.
    
    Below is a series of observations, in the order they occurred, followed by a question.  Your job is to analyze the observations carefully and then answer the question. 

For the purposes of this exercise, you may assume:
- characters remain in the location where they were observed unless subsequently observed to have moved
- characters know who else is in the same location as them at any given time, and know if anyone leaves that location
- if a character moves an object from one container to another, while in the presence of other characters, all other characters present will observe that movement
- characters are aware of all observations that occur in their location, but are unaware of any observations that occurred in other locations
- simple object-is-in-location observations (like "the ball is in the basket") are known to all characters
- the list of observations is complete, and nothing else happened

Explain your reasoning carefully before giving a final answer as a single lowercase word without punctuation.  You may explain any sources of uncertainty in your reasoning, but always give the most specific possible one-word final answer with your best guess, using the specific vocabulary used in the observations.

Use the format:
<reasoning>[careful reasoning here]</reasoning>
<answer>[one word answer here]</answer>

Actions:
{action_list}

Question:
{question.question}

Begin.
    """
    print(message_content)
    response = openai.ChatCompletion.create(
      model=OPEN_AI_MODEL,
      temperature=0,
      messages=[
        {
          "role": "system",
          "content": "You are a highly analytical, detail-oriented assistant."
        },
        {
          "role": "user",
          "content": message_content
        },
      ])

    gpt_response = response['choices'][0]['message']['content']
    print("GPT Response:", gpt_response)
    # parse out the answer from <answer> tags in gpt_response
    gpt_answer = gpt_response.split("<answer>")[1].split("</answer>")[0]
    print("GPT Answer:", gpt_answer)

    csv_writer.writerow([
      "\n".join(question.actions), question.question, question.answer,
      question.question_type, question.story_type, message_content,
      gpt_response, gpt_answer
    ])

    time.sleep(SLEEP_TIME)


if __name__ == "__main__":
  main()