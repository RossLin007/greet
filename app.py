import os
import openai
import gradio as gr
import pickle

# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = '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'

messages = [
    {"role": "system", "content": "You are a teacher"}
]


def openai_connect(input):
    global messages
    len(messages) > 50 and messages.pop(0)
    messages.append({"role": "user", "content": input})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    resp = response.choices[0]['message']['content'] or ''
    messages.append({"role": "assistant", "content": resp})
    return resp

def history_path(request: gr.Request):
    path = request.cookies and hash(request.cookies) or ''
    return f'/tmp/history_{path}.pkl'   

def save_history(history, request: gr.Request):
    path = history_path(request)    
    pickle.dump(history, open(path, 'wb'))


def load_history(request: gr.Request):
    path = history_path(request)
    if os.path.exists(path):
        history = pickle.load(open(path, 'rb'))
        if (history and len(history) <= 50):
            return history
    else:
        return []


def chat_with_ai(input, history, request: gr.Request):
    global messages
    history = load_history(request)
    output = openai_connect(input)
    output = output and f"""<pre style="font-size:14px;word-wrap:break-word;white-space:pre-wrap; ">{output}</pre>"""
    print('AI:', output)
    history.append((input, output))
    save_history(history,request)
    return history, history


def auth_contorl(username, password):
    auth = {'admin': "aexp123", "guest": "exp123"}
    return auth.get(username, False) and auth.get(username) == password and True


block = gr.Blocks(css="#chatbot {height: 100%;height:-webkit-fill-available;overflow: scroll;};")
block.title = "fGPT"
block.theme = "gradio/monochrome"


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

    with gr.Row():
        with gr.Column(min_width=200):
            message = gr.Textbox(
                placeholder='Type your message here...', lines=1, label='', every=float)
        with gr.Column(min_width=50):
            submit = gr.Button("SEND")

    state = gr.State()
    submit.click(chat_with_ai, inputs=[
                 message, state], outputs=[chatbot, state])
    #        .then(lambda x: message.update(value=''), None, [message])
    submit.click(lambda x: message.update(value=''), [submit], [message])
    message.submit(lambda x: message.update(value=''), [submit], [message])
    block.load(init_history, inputs=None, outputs=chatbot)

block.launch(debug=True,
             auth=auth_contorl,
             server_name="0.0.0.0",
             server_port=3500
             )
