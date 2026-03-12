import requests
import json
import time
import asyncio
import datetime
from openai import AsyncOpenAI
"""
from openai import OpenAI

client = OpenAI(
    api_key="MODELSCOPE_ACCESS_TOKEN", # 请替换成您的ModelScope Access Token
    base_url="https://api-inference.modelscope.cn/v1/"
)


response = client.chat.completions.create(
    model="Qwen/Qwen3.5-35B-A3B", # ModelScope Model-Id
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': '用python写一下快排'
        }
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end='', flush=True)

"""


botUrl = ""
botPort = 0
token = "114514"
headers = {"Authorization": f"Bearer {token}"}
last_real_id = 0
api_key = ""
timer_messages=[]

def add_timer_message(message):
    global timer_messages
    # 解析消息内容，提取时间和提醒内容
    try:
        print(f"GPT回复的消息: {message}")
        for line in message.splitlines():
            time_str, reminder_content = line.split(",", 1)
            time_str = time_str.strip()
            reminder_content = reminder_content.strip()
            # 将时间字符串转换为datetime对象
            reminder_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            # 将提醒内容和时间存储在数据库或内存中
            # 这里可以使用一个列表来存储定时消息
            timer_messages.append((reminder_time, reminder_content))
            print(f"定时消息已添加: {reminder_time} - {reminder_content}")
    except ValueError:
        print("消息格式错误，请使用 '时间 , 提醒内容' 的格式")

def check_timer_messages():
    global timer_messages
    current_time = datetime.datetime.now()
    for reminder_time, reminder_content in timer_messages:
        if current_time >= reminder_time:
            # 发送提醒消息
            print(f"发送提醒消息: {reminder_content}")
            requests.post(
                f"{botUrl}:{botPort}/send_group_msg",
                json={
                    "group_id": "1042964394",
                    "message": reminder_content
                },
                headers=headers
            )
            print(f"提醒: {reminder_content}")
            # 从列表中移除已发送的定时消息
            timer_messages.remove((reminder_time, reminder_content))

async def run_gpt_task(message):
    global api_key
    client  = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api-inference.modelscope.cn/v1/"
    )
    response = await client.chat.completions.create(
        model="Qwen/Qwen3.5-35B-A3B", # ModelScope Model-Id
        messages=[
            {
                'role': 'system',
                'content': '你是计算机8班的班级小助手,负责设置定时消息和转发消息,帮助同学们更好地使用机器人。'
            },
            {
                'role': 'user',
                'content': message+"\n, 阅读这段消息后，判断是否需要提醒同学们，如果需要，请回复 \"时间 , 提醒内容\" , 其中时间的格式为 \"2026-MM-DD HH:MM\",半角逗号,提前半小时，如果不需要提醒，请回复 \"不需要提醒\" ,不需要任何额外的文字"
            }
        ],
    )
    print(response.choices[0].message.content)
    add_timer_message(response.choices[0].message.content)

# 783463810
def get_message():
    request_string = """{
                    "group_id": "1019963716",
                    "message_seq": "textValue",
                    "count": 5,
                    "reverseOrder": true
                    }"""
    response = requests.post(f"{botUrl}:{botPort}/get_group_msg_history", data=request_string, headers=headers)
    if response.status_code == 200:
        data = response.json()
        list =[message for message in data["data"]["messages"]]
        return list
    else:
        print(f"Error: {response.status_code}")
        return []

def check_new_message(messages):
    global last_real_id
    message_queue = []
    if(len(messages) > 0):
        for message in messages:
            if int(message["real_seq"]) > last_real_id:
                message_queue.append(message)
                print(message["real_seq"])
        last_real_id = int(messages[-1]["real_seq"])
    return message_queue
def send_message(group_id="1042964394", message_queue=[]):
    for message in message_queue:
        time.sleep(1) # 每条消息间隔1秒发送
        if(message["message"].strip() == ""):
            continue

        print(message["message_id"])
        if not message["message"].startswith("[CQ:"):
            asyncio.run(run_gpt_task(message["message"]))
        response = requests.post(
            f"{botUrl}:{botPort}/forward_group_single_msg",
            json={
                "group_id": group_id,
                "message_id": message["message_id"]
            },
            headers=headers,
        )
        if response.status_code == 200:
            print(response.json())
        else:
            print(f"Error sending message {message['message_id']}: {response.status_code}")
    message_queue.clear()

def main():
    global token, botUrl, botPort, last_real_id, api_key, headers,timer_messages
    file = open("settings.json", "r")
    settings = json.load(file)
    botUrl = settings["botUrl"]
    botPort = settings["botPort"]
    token = settings["token"]
    last_real_id = settings["last_real_id"]
    api_key = settings.get("api_key", "")
    timer_messages = settings.get("timer_messages", [])
    # Refresh headers after loading runtime token.
    headers = {"Authorization": f"Bearer {token}"}

    file.close()
    
    while True: # 每5秒检查一次新消息
        messages = get_message()
        send_message(
        message_queue=check_new_message(messages))
        check_timer_messages()
        print("Loop completed, sleeping for 5 seconds...")
        file = open("settings.json","w") 
        file.write(json.dumps({
                "botUrl": botUrl,
                "botPort": botPort,
                "token": token,
                "last_real_id": last_real_id,
                "api_key": api_key,
                "timer_messages": timer_messages

        }))
        file.close()
        time.sleep(5) 

if __name__ == "__main__":
    main()