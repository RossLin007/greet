import os
import sys
import openai
import gradio as gr
import pickle
import logging
from openai.error import APIError

log_format = "%(asctime)s::%(levelname)s::%(name)s::"\
             "%(filename)s::%(lineno)d::%(message)s"
logging.basicConfig(level='DEBUG', format=log_format)
logger = logging.getLogger(__name__)


# openai.api_key = os.getenv("OPENAI_API_KEY")
# print(openai.api_key)
openai.api_key = "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"
messages = [
    {"role": "system", "content": """你是个专家。你中文英文都非常好。Your task is to be my brainstorming partner and provide creative ideas and suggestions for a given topic or problem. Your response should include original, unique, and relevant ideas that could help solve the problem or further explore the topic in an interesting way. And You also need to consider both sides of the problem. Please note that your response should also take into account any specific requirements or constraints of the task."""}
]


def openai_connect(input):
    global messages

    #len(messages) > 5 and messages.pop(1)
    if sys.getsizeof(messages) > 15000:
        messages.pop(1)

    messages.append({"role": "user", "content": input})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
            max_tokens=600,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        logger.info(response)
        if response.usage.total_tokens > 3500 :
            messages.pop(1)
        resp = response.choices[0]['message']['content'] or ''
    except APIError as e:
        resp = 'response error'
        logger.error(e)

    messages.append({"role": "assistant", "content": resp})
    logger.info(f"input: {input}, output: {resp}")
    logger.info(f"prompt messages: {messages}")

    return resp


def history_path(request: gr.Request):
    path = request.cookies.__dict__.get("access-token-unsecure")
    return f'/tmp/history_{request.client.host}{hash(path)}.pkl'


def save_history(history, request: gr.Request):
    path = history_path(request)
    logger.info(f"""save to {path}:{history}""")
    pickle.dump(history, open(path, 'wb'))


def load_history(request: gr.Request):
    path = history_path(request)
    # print("load history from: %s" % path)
    if os.path.exists(path):
        history = pickle.load(open(path, 'rb'))
        if (history and len(history)):
            return history
    else:
        return []


def chat_with_ai(input, history, request: gr.Request):
    global messages
    history = load_history(request)
    output = openai_connect(input)
    output = output and f"""<pre style="font-size:14px;word-wrap:break-word;white-space:pre-wrap; ">{output}</pre>"""
    history.append((input, output))
    save_history(history, request)
    return history, history


def auth_contorl(username, password):
    auth = {'admin': "aexp123", "guest": "exp123"}
    return auth.get(username, False) and auth.get(username) == password and True


block = gr.Blocks(
    css="""
    #component-0 {justify-content:space-between;height:-webkit-fill-available;}
    #chatbot {height:500px !important;height:-webkit-fill-available;overflow:scroll !important;;}
    footer {display: none !important;}
    """
)
block.title = "fGPT"

def init_history(request: gr.Request):
    return load_history(request)


with block:
    # history = load_history()
    chatbot = gr.Chatbot(
        #   value=history,
        elem_id='chatbot',
        label="ChatGPT",
        every=float)
    chatbot.color_map = ["green", "pink"]

    message = gr.Textbox(
        placeholder='Type your message here...', lines=1, label='', every=float)
    submit = gr.Button("SEND")

    state = gr.State()
    submit.click(chat_with_ai, inputs=[
                 message, state], outputs=[chatbot, state])
    message.submit(chat_with_ai, inputs=[
        message, state], outputs=[chatbot, state]).update(value='')
    #        .then(lambda x: message.update(value=''), None, [message])
    submit.click(lambda x: message.update(value=''), [submit], [message])
    # message.submit(lambda x: message.update(value=''), [submit], [message])

    block.load(init_history, inputs=None, outputs=chatbot)

block.launch(debug=True,
             auth=auth_contorl,
             server_name="0.0.0.0",
             server_port=3500,
             show_api=False
             )
