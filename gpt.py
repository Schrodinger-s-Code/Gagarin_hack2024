import config
import requests

def ask_gpt(collection, mode='continue'):
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {config.TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{config.FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 200
        },
        "messages": []
    }

    for row in collection:
        content = row['content']

        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + config.CONTINUE_STORY
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + config.END_STORY

        data["messages"].append({
            "role": row["role"],
            "text": content
        })

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            result = f"Status code {response.status_code}."
            return result
        result = response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."
    return result