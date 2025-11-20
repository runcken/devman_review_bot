# Devman Review Bot
A Telegram bot for tracking completed lessons in Devman's course.


## How to install

Clone repository to your local device. To avoid problems with installing required additinal packages, its strongly to use a virtual environment [virtualenv/venv](https://docs.python.org/3/library/venv.html), for example:

```bash
python3 -m venv myenv
source myenv/bin/activate
```

## Environment

### Requirements

Python3.12 should be already installed. Then use pip (or pip3, if there is a conflict with Python2) to install dependencies:

```bash
pip install -r requirements.txt
```

The script uses additinal packages:

- python-telegram-bot==13.7
- urllib3==1.26.18
- requests==2.32.5
- environs==14.5.0

### Environment variables

- DEVMAN_TOKEN,
- TG_TOKEN

1. Put `.env` file near `main.py`.
2. `.env` contains text data without quotes.


## Run

Launch on Linux(Python 3) or Windows:

```bash
python3 main.py your-telegram-chat-id
```

When lesson checks appear, a notification about them will be sent to Telegram


## Notes

The file with the contents of these environment variables isnt included in the repository.

## Project Goals

The code is written for educational purposes on online-course for web-developers dvmn.org.
