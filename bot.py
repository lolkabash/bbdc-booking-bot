import requests
from config import load_config
from discordwebhook import Discord


def get_update(token):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    return requests.get(url)


def send_message_tele(text, token, chat_id):
    url = (
        f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
    )
    return requests.get(url)


def send_message_disc(text, webhook):
    discord = Discord(url=webhook)
    discord.post(content=text, username="BBDC Slots")
    return


def test_bot_tele():
    config = load_config("config.yaml")

    bot_token = config["telegram"]["token"]
    chat_id = config["telegram"]["chat_id"]

    if not bot_token or not chat_id:
        print("no telegram token or no chat_id")
        return

    text = "Hello!\ntest from python"
    r = send_message_tele(text, bot_token, chat_id)
    print(r.status_code)


def test_bot_disc():
    config = load_config("config.yaml")

    webhook = config["discord"]["webhook"]
    if not webhook:
        print("no discord webhook")
        return

    text = "Hello!\ntest from python"
    send_message_disc(text, webhook)


def get_chat_id():
    config = load_config("config.yaml")
    bot_token = config["telegram"]["token"]

    if not bot_token:
        print("no token")
        return

    r = get_update(bot_token)
    print(r.json())


if __name__ == "__main__":
    get_chat_id()
    test_bot_tele()
    test_bot_disc()
