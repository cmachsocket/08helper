import requests
import json
import time

botUrl = ""
botPort = 0
token = "114514"
headers = {"Authorization": f"Bearer {token}"}
last_real_id = 0

def get_message(group_id="783463810", count=5):
    request_string = """{
                    "group_id": "783463810",
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
def send_message(group_id="817494034", message_queue=[]):
    for message in message_queue:
        time.sleep(1) # 每条消息间隔1秒发送

        print(message["message_id"])
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
    global token, botUrl, botPort , last_real_id
    file=open("settings.json","r")
    settings=json.load(file)
    botUrl = settings["botUrl"]
    botPort = settings["botPort"]
    token = settings["token"]
    last_real_id = settings["last_real_id"]
    file.close()

    while True: # 每5秒检查一次新消息
        messages = get_message()
        send_message(
        message_queue=check_new_message(messages))
        print("Checked for new messages.")
        file = open("settings.json","w") 
        file.write(json.dumps({
                "botUrl": botUrl,
                "botPort": botPort,
                "token": token,
                "last_real_id": last_real_id
        }))
        file.close()
        time.sleep(5) 

if __name__ == "__main__":
    main()