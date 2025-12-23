import argparse
import logging
import requests
import telegram
import time
from environs import Env


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.tg_bot = tg_bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry[:4096])
        except Exception as e:
            print(f'Failed to sent log to Telegram: {e}')


# logger = logging.getLogger()


def format_review_message(devman_answer):
    attempt = devman_answer['new_attempts'][0]

    lesson_title = attempt['lesson_title']
    is_negative = attempt['is_negative']
    lesson_url = attempt['lesson_url']

    status = (
        'К сожалению, в работе нашлись ошибки'
        if is_negative
        else 'Работа принята'
    )

    message = f'''Преподаватель проверил работу: "{lesson_title}",
{lesson_url}. {status}.'''

    return message.strip()


def send_devman_review(devman_token, bot, tg_chat_id):
    api_url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': devman_token}

    params = {}
    timestamp = None

    bot.send_message(
        chat_id=tg_chat_id,
        text='...бот начал отслеживание проверок...'
    )

    while True:
        try:
            if timestamp:
                params['timestamp'] = timestamp
            else:
                params = {}

            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=90
            )
            response.raise_for_status()

            devman_answer = response.json()

            if devman_answer.get('status') == 'found':
                logging.info('Найдена новая проверка')
                message = format_review_message(devman_answer)
                logging.info(f'Сформировано сообщение: {message}')

                bot.send_message(
                    chat_id=tg_chat_id,
                    text=message,
                    disable_web_page_preview=False
                )

                timestamp = devman_answer.get('last_attempt_timestamp')

            elif devman_answer.get('status') == 'timeout':
                timestamp = devman_answer.get('timestamp_to_request')
                logging.debug('Таймаут сервера, переподключение...')

        except requests.exceptions.ReadTimeout:
            continue

        except requests.exceptions.HTTPError as error:
            if response.status_code == 401:
                logging.error('Ошибка авторизации: неверный токен Devman')
                return
            else:
                logging.error(f'Ошибка API Devman: {error}')
                time.sleep(10)

        except requests.exceptions.ConnectionError as error:
            logging.error(f'Ошибка подключения: {error}')
            time.sleep(10)

        except ValueError as error:
            logging.error(f'Ошибка обработки данных: {error}')
            time.sleep(5)

        except Exception as error:
            logging.error(f'Неожиданная ошибка: {error}')
            time.sleep(10)


def main():
    env = Env()
    env.read_env()

    devman_token = env.str('DEVMAN_TOKEN')
    tg_token = env.str('TG_TOKEN')
    parser = argparse.ArgumentParser(
        description='Бот для отслеживания проверок Devman в Telegram'
    )
    parser.add_argument('chat_id', help='ID чата в Telegram')
    args = parser.parse_args()
    tg_chat_id = args.chat_id

    print('Запуск бота отслеживания проверок Devman...')
    print(f'Chat ID: {tg_chat_id}')

    try:
        bot = telegram.Bot(token=tg_token)
        bot_info = bot.get_me()
        bot = 4 / 0
        print(f'Бот @{bot_info.username} успешно подключен')
    except Exception as error:
        print(f'Ошибка подключения к Telegram: {error}')
        return

    logging.basicConfig(
       format='%(asctime)s - %(levelname)s - %(message)s',
       level=logging.INFO
    )
    root_logger = logging.getLogger()
    telegram_handler = TelegramLogsHandler(bot, tg_chat_id)
    telegram_handler.setLevel(logging.INFO)
    telegram_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(telegram_handler)
    root_logger.info('логгирование вроде работает')


    try:
        send_devman_review(devman_token, bot, tg_chat_id)
    except KeyboardInterrupt:
        bot.send_message(
            chat_id=tg_chat_id,
            text='...бот остановлен'
        )
        print('Бот остановлен')


if __name__ == '__main__':
    main()
