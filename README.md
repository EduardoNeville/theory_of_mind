# GPT Theory of Mind

Theory of mind (ToM) is the ability to attribute mental states to ourselves and others; accurately predicting other people’s beliefs, intents, desires and emotions is key to navigating everyday life. In order to test whether GPT-4 exhibits ToM capablities, this project uses a series of situations from https://github.com/facebookresearch/ToMi and asks GPT to answer questions on them. The scenarios and questions, along with descriptions are stored in `data/questions/test.trace` and `data/questions/test.txt`. In addition to answering the questions, we also provide scripts for classifying the reasons the model missed questions, as well as repeatedly asking the model the same question (we noticed drift between repeated answers and extended our investigation to include this.

Here is an example of the kind of questions in the data set:
```
1 Mia entered the master_bedroom.
2 Elizabeth entered the staircase.
3 Emily entered the staircase.
4 The tangerine is in the box.
5 Elizabeth exited the staircase.
6 Emily likes the apple
7 Emily moved the tangerine to the envelope.
8 Elizabeth entered the master_bedroom.

Q: Where will Elizabeth look for the tangerine?
A: Box
```
# Directory Layout
## `scripts/main.py`
This script runs the main question/answer loop. TWe select random questions and ask ChatGPT to answer. You can configure the number of questions and which version of the model you use at runtime using the CLI. To run the main research loop (using the same model we did), use the following command:
`venv/bin/python scripts/main.py --n_questions 10 --model gpt-4-0314`

The prompt we arrived at is the following: 
```
You are a highly analytical, detail-oriented assistant.
    
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
```

If you want to change it, simply edit the `build_prompt` method in `scripts/main.py`.

GPT responds in XML with both a single word answer and the reasoning. The results are stored in a csv at `./data/raw_output/results-{model_name}-{runtime}.csv`. Values included are:
```
actions,question,answer,question_type,story_type,gpt_answer 
```

Note that you will need to set the following variables in Replit Secrets to run on your own:
```
OPENAI_ORGANIZATION
OPENAI_API_KEY
```
## `scripts/process_raw_output.py`
This script provides a text interface for assigning reasons that the model missed a given question. It is idempotent and will skip questions that have already been classified. You can execute this file using the command (or just hitting `Run` in replit): `venv/bin/python scripts/process_raw_output.py`. This will create a new file, `./data/classified_results.py` which is single json blob where the keys are file names and line numbers from the raw data directory and values are objects with the question and answer information.

## `scripts/repeat_prompt.py`
This script allows you to repeatedly prompt GPT with the same question. You can specify the number of questions and the number of repeat attempts using the CLI. You can run the script like: `venv/bin/python scripts/repeat_prompt.py --n_questions 10 --n_reps 5`

Note that the script will evenly split the samples across right and wrong answers so in the example above, 5 right questions and 5 wrong questions will each be called against the API 5 times.

