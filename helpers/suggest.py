import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def suggest(niche):
  response = openai.Completion.create(
    model="text-davinci-002",
    prompt="Write a search engine optimized 140 word count meta description for my {} website.".format(niche),
    temperature=0.8,
    max_tokens=150,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.3
  )

  return {'suggestion' : response['choices'][0]['text']}