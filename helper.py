import requests
import json
import time
import asyncio
import datetime
import os
from openai import AsyncOpenAI


botUrl = ""
botPort = 0
token = "114514"
headers = {"Authorization": f"Bearer {token}"}
last_real_id = 0
api_key = ""
timer_messages=[]


def load_env_file(file_path=".env"):
    try:
        with open(file_path, "r") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass

def add_timer_message(message):
    global timer_messages
    # 解析消息内容，提取时间和提醒内容
    need_forward = True
    try:
        print(f"GPT回复的消息: {message}")
        for line in message.splitlines():
            if line.strip() == "不需要转发":
                print("GPT回复: 不需要转发")
                need_forward = False
                continue
            elif line.strip() == "需要转发":
                continue
            time_str, reminder_content = line.split(",", 1)
            time_str = time_str.strip()
            reminder_content = reminder_content.strip()
            # 将时间字符串转换为datetime对象
            reminder_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            # 将提醒内容和时间存储在数据库或内存中
            # 这里可以使用一个列表来存储定时消息
            timer_messages.append((reminder_time, reminder_content))
            print(f"定时消息已添加: {reminder_time} - {reminder_content}")
        return need_forward
    except ValueError:
        if message.strip() == "不需要提醒":
            print("GPT回复: 不需要提醒")
        else:
            send_message_to_manager(f"GPT回复的消息格式错误: {message}")
        return need_forward
def check_timer_messages():
    global timer_messages
    current_time = datetime.datetime.now()
    for reminder_time, reminder_content in timer_messages:
        if reminder_time.year != current_time.year or reminder_time.month != current_time.month or reminder_time.day != current_time.day:
            timer_messages.remove((reminder_time, reminder_content))
            continue
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

async def run_gpt_task_with_retry(message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await run_gpt_task(message)
        except Exception as e:
            print(f"API调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print("API重试耗尽，跳过该消息")
                return True

async def run_gpt_task(message):
    global api_key
    client  = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.minimaxi.com/v1"
    )
    response = await client.chat.completions.create(
        model="MiniMax-M2.7", # ModelScope Model-Id
        messages=[
            {
                'role': 'system',
                'content': '你是计算机8班的班级小助手,负责设置定时消息和转发消息,帮助同学们更好地使用机器人。当前时间是 '+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            {
                'role': 'user',
                'content': message+"\n, 阅读这段消息后，先判断是否需要转发 ， 如果需要转发，请回复 \"需要转发\" ，如果不需要转发，请回复 \"不需要转发\" 。同时，判断是否需要提醒同学们，如果需要，请换一行回复 \"时间 , 提醒内容\" , 其中时间的格式为 \"YYYY-MM-DD HH:MM\",半角逗号,提前半小时，如果不需要提醒，请换一行回复 \"不需要提醒\" ,不需要任何额外的文字"
            }
        ],
        extra_body={
            "reasoning_split": True
        }
    )
    print(response.choices[0].message.content)
    return add_timer_message(response.choices[0].message.content)

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
            need_forward = asyncio.run(run_gpt_task_with_retry(message["message"]))
            if not need_forward:
                continue
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

def send_message_to_manager(message):
    response = requests.post(
        f"{botUrl}:{botPort}/send_private_msg",
        json={
            "user_id": "3077906125",
            "message": message
        },
        headers=headers,
    )
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error sending message to manager: {response.status_code}")

def get_message_from_manager(manager_id = "3077906125"):
    pass

def main():
    global token, botUrl, botPort, last_real_id, api_key, headers,timer_messages
    load_env_file()
    file = open("settings.json", "r")
    settings = json.load(file)
    botUrl = settings["botUrl"]
    botPort = settings["botPort"]
    token = settings["token"]
    last_real_id = settings["last_real_id"]
    api_key = os.getenv("API_KEY", "")
    timer_messages_str = settings.get("timer_messages", [])
    timer_messages = [(datetime.datetime.strptime(item[0], "%Y-%m-%d %H:%M"), item[1]) for item in timer_messages_str]
    # Refresh headers after loading runtime token.
    headers = {"Authorization": f"Bearer {token}"}

    file.close()
    
    while True: # 每5秒检查一次新消息
        try :
            messages = get_message()
        except Exception as e:
            print(f"Error getting messages: {e}")
            time.sleep(5)
            continue
        try:
            send_message(
            message_queue=check_new_message(messages))
        except Exception as e:
            print(f"send_message出错: {e}")
            time.sleep(5)
            continue
        check_timer_messages()
        print("Loop completed, sleeping for 5 seconds...")
        file = open("settings.json","w") 
        file.write(json.dumps({
                "botUrl": botUrl,
                "botPort": botPort,
                "token": token,
                "last_real_id": last_real_id,
                "timer_messages": [(item[0].strftime("%Y-%m-%d %H:%M"), item[1]) for item in timer_messages]

        }))
        file.close()
        time.sleep(5) 

if __name__ == "__main__":
    main()


# proot-distro sh napcat -- bash -c "xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox"