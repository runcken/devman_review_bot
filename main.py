import argparse
import requests
import telegram
import time
from environs import Env


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


def send_tg_notification(bot, tg_chat_id, message):
    try:
        bot.send_message(
            chat_id=tg_chat_id,
            text=message,
            disable_web_page_preview=False
        )
        print('Уведомление отправлено')
        return True
    except telegram.error.TelegramError:
        print('Уведомление не отправлено')
        return False


def devman_request(devman_token, bot, tg_chat_id):
    api_url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': devman_token}

    params = {}
    timestamp = None

    send_tg_notification(
        bot,
        tg_chat_id,
        '...бот начал отслеживание проверок...'
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
                print('Найдена новая проверка')
                message = format_review_message(devman_answer)
                print(message)
                send_tg_notification(bot, tg_chat_id, message)
                timestamp = devman_answer.get('last_attempt_timestamp')

            elif devman_answer.get('status') == 'timeout':
                timestamp = devman_answer.get('timestamp_to_request')
                print('Переподключение, ожидание проверок...')

        except requests.exceptions.ReadTimeout:
            print('Таймаут запроса, продолжаем ожидание...')
            continue

        except requests.exceptions.HTTPError as error:
            if response.status_code == 401:
                print('Ошибка: неверный токен авторизации')
            else:
                print(f'Ошибка API: {error}')
                time.sleep(10)

        except requests.exceptions.ConnectionError as error:
            print(f'Ошибка сети: {error}')
            time.sleep(10)

        except ValueError as error:
            print(f'Ошибка данных: {error}')
            time.sleep(5)

        except Exception as error:
            print(f'Неожиданная ошибка: {error}')
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
        print(f'Бот @{bot_info.username} успешно подключен')
    except Exception as e:
        print(f'Ошибка подключения к Telegram: {e}')

    try:
        devman_request(devman_token, bot, tg_chat_id)
    except KeyboardInterrupt:
        send_tg_notification(bot, tg_chat_id, '...бот остановлен')
        print('Бот остановлен')


if __name__ == '__main__':
    main()
