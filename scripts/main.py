import csv
import os
import random
import time
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer


import openai

# OPEN AI API setup based on API Key and ORG ID
# These are set in env variables - on Replit they are in secrets; written
# to raise a key error if the values aren't set
# openai.organization = os.environ["OPENAI_ORGANIZATION"]
openai.api_key = os.environ["OPENAI_API_KEY"]

OUTPUT_DIR = Path(f"{os.path.dirname(__file__)}/../data/raw_output")
QUESTION_DIR = Path(f"{os.path.dirname(__file__)}/../data/questions")


@dataclass
class Question:
    question_type: str
    story_type: str
    actions: tuple[str]
    question: str
    answer: str


def build_prompt(question: Question) -> str:
    """Return a prompt given a question"""
    action_list = "\n".join(question.actions)
    return f"""You are a highly analytical, detail-oriented assistant.
    
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
    
    Begin."""


def get_descriptions(file_path: Path) -> list[str]:
    """Load question descriptions which are metadata about the question
    including the question and story type
    """
    descriptions = []
    with open(file_path, "r") as description_file:
        for line in description_file:
            line = line.strip()
            classifications = line.split(",")
            question_type = classifications[-2]
            story_type = classifications[-1]

            descriptions.append((question_type, story_type))

    return descriptions


def get_questions(file_path: Path) -> list[tuple]:
    """Load question data which consits of 3 parts:
    - actions: tuple of strings that contain list of facts
    - question: string that asks a question about the actions
    - answer: string that is the correct answer to the question
    """
    questions = []
    with open(file_path, "r") as questions_file:
        actions = []
        for line in questions_file:
            line = line.strip()

            # This is the quetion and end of this sceanrio
            if "?" in line:
                # Get question and answer
                question_and_answer = line.split("?")
                question = question_and_answer[0] + "?"
                answer = question_and_answer[1].strip().replace("\t", " ").split(" ")[0]

                questions.append((tuple(actions), question, answer))
                actions = []
            else:
                actions.append(line)

    return questions


def main(n_questions: int, model_name: str, sleep_time: int, is_mistral: bool) -> None:
    """Runs the core loop for getting GPT model to run theory of mind tasks.
    Randomly samples questions from the available input then build prompt for
    the question, ask GPT and record answer in flat csv file. You can control
    the number of questions, model used and time between requests using the
    CLI arguments
    """
    descriptions: list[tuple] = get_descriptions(QUESTION_DIR / "test.trace")
    question_data: list[tuple] = get_questions(QUESTION_DIR / "test.txt")

    # Combine into questions list
    questions = []
    # for i in range(len(descriptions)):
    for description, qd in zip(descriptions, question_data):
        question_type, story_type = description
        actions, question, answer = qd
        questions.append(Question(question_type, story_type, actions, question, answer))

    # create output file including writing header
    time_string = time.strftime("%Y-%m-%d_%H%M%S")
    output_file = OUTPUT_DIR / f"results-{model_name}-{time_string}.csv"
    csvfile = open(output_file, "a")
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(
        [
            "actions",
            "question",
            "answer",
            "question_type",
            "story_type",
            "gpt_prompt",
            "gpt_response",
            "gpt_answer",
        ]
    )

    # now randomly choose index questions; make sure you don't hit the same
    # one twice.
    # TODO: implement so that you don't get dupes across separate runs
    visited_index = set()
    for i in range(n_questions):
        print("Selecting Question:", i + 1, "of", n_questions)

        idx = random.choice(list(range(len(descriptions))))
        while idx in visited_index:
            idx = random.choice(list(range(len(descriptions))))

        print(f"Chose Random Index: {idx}")
        visited_index.add(idx)

        question = questions[idx]
        prompt = build_prompt(question)
        print(prompt)

        gpt_answer, gpt_response = (
            generate_openai_completion(model_name, prompt)
            if not is_mistral
            else generate_mistral_completion(model_name, prompt)
        )

        csv_writer.writerow(
            [
                "\n".join(question.actions),
                question.question,
                question.answer,
                question.question_type,
                question.story_type,
                prompt,
                gpt_response,
                gpt_answer,
            ]
        )

        time.sleep(sleep_time)


def generate_openai_completion(model_name, prompt):
    response = openai.ChatCompletion.create(
        model=model_name,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a highly analytical, detail-oriented assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    gpt_response = response["choices"][0]["message"]["content"]
    print("GPT Response:", gpt_response)
    # parse out the answer from <answer> tags in gpt_response
    return parse_response(gpt_response)


def parse_response(gpt_response):
    try:
        gpt_answer = gpt_response.split("<answer>")[1].split("</answer>")[0]
    except:
        gpt_answer = ""
    print("GPT Answer:", gpt_answer, end="\n")
    return gpt_answer, gpt_response


def generate_mistral_completion(model_name, prompt):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    model_inputs = tokenizer(prompt, return_tensors="pt")

    generated_ids = model.generate(
        **model_inputs, max_length=tokenizer.model_max_length
    )
    gpt_response = tokenizer.batch_decode(
        generated_ids[:, model_inputs["input_ids"].numel() :]
    )[0]
    print(gpt_response)

    return parse_response(gpt_response)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="This script uses OpenAI API to answer a series of questions based on a given set of observations."
    )

    parser.add_argument(
        "-n",
        "--n_questions",
        type=int,
        default=100,
        required=False,
        help="The number of questions the model will answer. Default is 100.",
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-4",
        required=False,
        help="The name of the OpenAI model to be used for question answering. Default is gpt-4.",
    )

    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=0,
        required=False,
        help="The amount of time in seconds the program will sleep after each question. Default is 0.",
    )

    parser.add_argument(
        "--huggingface",
        type=bool,
        required=False,
        default=False,
        help="Whether the model should be read from Huggingface.",
    )

    args = parser.parse_args()
    main(args.n_questions, args.model, args.sleep, args.huggingface)
