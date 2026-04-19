import requests
import time
import argparse


botUrl = "http://192.168.31.135"
botPort = 3000
token = "114514"
headers = {"Authorization": f"Bearer {token}"}
last_real_id = 0
source_group_id = "1092143423"




def get_message(group_id, message_seq=None):
    if message_seq is None:
        message_seq = str(last_real_id) if last_real_id > 0 else "0"

    payload = {
        "group_id": group_id,
        "message_seq": message_seq,
        "count": 5,
        "reverseOrder": True,
    }
    response = requests.post(
        f"{botUrl}:{botPort}/get_group_msg_history",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if response.status_code == 200:
        data = response.json()
        return [message for message in data.get("data", {}).get("messages", [])]
    else:
        body_preview = (response.text or "").strip()[:500]
        print(f"Error: {response.status_code}, payload={payload}, response={body_preview}")
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
def get_message_type(messages):
    for message in messages:
        print(message.get("message_type", "unknown"))


def main():
    global token, botUrl, botPort, last_real_id, headers, source_group_id
    # Refresh headers after loading runtime token.
    headers = {"Authorization": f"Bearer {token}"}
    while True: # 每5秒检查一次新消息
        try :
            messages = get_message(source_group_id)
        except Exception as e:
            print(f"Error getting messages: {e}")
            time.sleep(5)
            continue
        try:
            get_message_type(
            messages=check_new_message(messages))
        except Exception as e:
            print(f"send_message出错: {e}")
            time.sleep(5)
            continue
        print("Loop completed, sleeping for 5 seconds...")
        time.sleep(5) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Message forwarding helper")
    parser.add_argument(
        "--source-group-id",
        type=str,
        default="1019963716",
        help="Source group id for polling message history",
    )
    parser.add_argument(
        "--last-real-id",
        type=int,
        default=0,
        help="Initialize last_real_id before polling messages",
    )
    parser.add_argument(
        "--message-seq",
        type=str,
        default=None,
        help="Optional message_seq for get_group_msg_history (default: use last_real_id)",
    )
    args = parser.parse_args()
    source_group_id = args.source_group_id
    last_real_id = args.last_real_id
    main()


# proot-distro sh napcat -- bash -c "xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox"