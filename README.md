# Milestone Monitor

## Usage

We've created a personal goal tracking chatbot called Milestone Monitor that anyone can chat with, simply by texting (number here once ready). Milestone Monitor uses GPT-powered capabilities to keep track of any goals, tasks, or habits you have, as well as send you tips and reminders regularly.

## Deploying Locally (WIP)

_Note: you will need Twilio, OpenAI, Pinecone, and Cohere accounts in order to do this_

1. Setting up ngrok:

- Install ngrok [here](https://ngrok.com/download) if you don't already have it, and follow [these steps](https://dashboard.ngrok.com/get-started/setup) to setup
- Instead of forwarding to port 80, use port 8000 (for Django), so the last command should be `ngrok http 8000`
- Copy the forwarding URL for later (should be `XXXXX.ngrok-free.app`, without the `https://`)

2. Configuring Twilio:

After getting an active number, you will need to go to `Configure > Messaging Configuration` and do the following:

- Set "Configure with" and "A message comes in" to the default settings (should be a webhook)
- Set the URL to `{your ngrok link}/sms/`
- Make sure the last field is `POST` and not `GET`
- Finally, make sure to save the configuration

3. Setup Cohere and Pinecone (should be completely free):

- You can get your Cohere API key here: https://dashboard.cohere.ai/api-keys
- You will need to set up a Pinecone database here: https://app.pinecone.io/
  - Name the index `milestone-monitor`
  - Set the embedding size to 1024 (needs to line up with the Cohere model you're using)
  - Choose P1 for the pod type (not sure if this matters for the starter plan though)
  - Make sure the similarity metric is `cosine`
  - You will also need to copy your own API key (left sidebar) as `PINECONE_API_KEY`, along with the environment beside it as `PINECONE_ENV`

4. Create a `.env` folder in the top directory with the following entries:

```
TWILIO_ACCOUNT_SID={Twilio account SID}
TWILIO_AUTH_TOKEN={Twilio authentication token}
MESSAGING_SERVICE_SID={Twilio messaging service SID}
REDIS_URL=redis://localhost/
POSTGRES_USER={your postgres user}
POSTGRES_PASSWORD={your postgres password}
POSTGRES_DB={your postgres database name}
NGROK_FORWARDING={ngrok forwarding URL here}

OPENAI_API_KEY={OpenAI API key here}
COHERE_API_KEY={Cohere API key here}
PINECONE_API_KEY={Pinecone API key here}
PINECONE_ENV={Pinecone environmnet key here}
PINECONE_INDEX=`milestone-monitor`
```

5. Open a terminal in this directory:

- `cd milestone-monitor` (move into the second inner `milestone-monitor` folder)
- `pipenv shell`
- `pipenv install`

6. Open a second terminal, and `cd` into the inner `milestone-monitor` folder:

- Make sure Docker Desktop is open, and run `docker-compose up`
- `python3 manage.py migrate` (in the original terminal window)
- `./runserver.sh` to run the server
- If you would like to listen to the logs for the Celery workers, you can use `tail -f celery.worker.log` in a separate terminal

## Development conventions

**User IDs**

- By default we should refer to a user using an _integer_ containing all of the digits in the phone number
- For requests (with Twilio), the phone number will have a `+` and be in the form of a string, so we should immediately
  convert this to an integer
