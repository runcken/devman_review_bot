import requests


if __name__ == '__main__':
    token = '21fdb9f883732ce30e7ecaa037afc2f907680115'
    api_url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': token}
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    print(answer)
    print(answer['new_attempts'][0])