# BBDC-Booking-Bot
Program help to check and book the available slots in BBDC (Bukit Batok Driving Centre), and send notification to your phone via Telegram/Discord.

<img src="banner.png" width=800 height=278/>

# Update
* **2023 June**: Works with the [new BBDC page](https://booking.bbdc.sg/) that requires captcha.

# Prerequisites
* Python3
* [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)
* [Telegram Bot](https://t.me/botfather)

# Setup

## Clone the repo
```sh
$ git clone https://github.com/lolkabash/bbdc-booking-bot.git
$ cd bbdc-booking-bot
```
## Create virtual environment and source the environment
```sh
# create virtual environment
$ python3 -m venv env
# activate the environment
$ source env/bin/activate
```

## Install dependencies
```sh
$ pip install -r requirement.txt
```

## Create your telegram bot
Follow this [post](https://dev.to/rizkyrajitha/get-notifications-with-telegram-bot-537l) to create your telegram bot

## Fill in your information
Please fill in the following in `new_config.yaml` and rename it to `config.yaml` when done:
* `Interval` for checking the slots (example: every 1 min)
* BBDC `username` and `password`
* Wanted `month` (example: `202306` for June 2023)
* Wanted `sessions` in list form (example: `[3, 4, 5, 6]` for Sessions 3, 4, 5, 6)
* Enable auto-solving `login` and `booking` captchas with Tesseract OCR
* `Enable_booking` or notifications only
* Telegram Bot `token` and `chat_id` (optional if `enabled`)
* Discord `webhook` url (optional if `enabled`)

# Run the program
```sh
$ python3 main.py
```

# Reference
* https://github.com/lizzzcai/bbdc-booking-bot