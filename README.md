# GPT Proof

This Python script uses a series of situations from https://github.com/facebookresearch/ToMi and asks GPT to answer questions on them. 

The scenarios and questions, along with descriptions are stored in `data/questions/test.trace` and `data/questions/test.txt`. 

The script will select 400 random questions and ask ChatGPT to answer. 

The prompt given to ChatGPT is in the following format:

```
  The following text will list a series of actions taken by different individuals, followed by a question about those actions. Please provide your answer to the question as a single lowercase word without punctuation. 
  
    Actions:
    {list of actions}
  
    Question:
    {question}
```


For example:

```
  The following text will list a series of actions taken by different individuals, followed by a question about those actions. Please provide your answer to the question as a single lowercase word without punctuation. 
  
  Actions:
  1 Jackson entered the hall.
  2 Chloe entered the hall.
  3 The boots is in the bathtub.
  4 Jackson exited the hall.
  5 Jackson entered the dining_room.
  6 Chloe moved the boots to the pantry.
  
  Question:
  7 Where will Chloe look for the boots?
```

ChatGPT will send back a single word response for the answer. 

Results are stored in results.csv. 

Values included are:
```
actions,question,answer,question_type,story_type, gpt_answer 
```

Example result row would look like:

```
1 Ella entered the bathroom. 2 Ella dislikes the shoes 3 Olivia entered the bathroom. 4 Ella loves the socks 5 Elizabeth entered the bathroom. 6 The socks is in the cupboard. 7 Ella moved the socks to the envelope. 8 Elizabeth exited the bathroom. 9 Olivia exited the bathroom. 10 Ella exited the bathroom. 11 Elizabeth entered the bathroom.,12 Where is the socks really?,envelope,reality,second_order_false_belief,envelope

```

Here is an example CSV file on Google Sheets. This one was run with GPT 3.5 Turbo. 
https://docs.google.com/spreadsheets/d/1kp9uF__tHxLX3kBqRzqyGazUpR0JzPE0Qn3Ic3D4FF4/edit?usp=sharing


You will need to set the following variables in Replit Secrets to run on your own:
```
OPENAI_ORGANIZATION
OPENAI_API_KEY
```

And if you want to use GPT4, change line 13:
```
OPEN_AI_MODEL = "gpt-3.5-turbo"
```