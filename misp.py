import requests
import slack
import os

SLACK_TOKEN = os.environ["SLACK_API_TOKEN"]
SLACK_CHANNEL = os.environ["SLACK_CHANNEL"]

misp_api_key = os.environ["MISP_API_KEY"]
base_url = os.environ["MISP_BASE_URL"]


def misp_get(indicator):
    path = "/events/index/searchall:{}".format(indicator)
    url = base_url + path
    misp_results = requests.get(url, headers={"Authorization": misp_api_key, "Accept": "application/json"}).json()
    return misp_results


def handler(event, context):
    try:
        channel = event['body']['channel_id']
        indicator = event['body']['text']
        if not indicator:
            return "Please enter an input"

        ## first message to start thread + avoid timeout
        client = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])
        bot_message = '```Getting results for indicator: {}```'.format(indicator)
        response = client.chat_postMessage(channel=channel, text=bot_message)
        thread_ts = response["ts"]

        ## get MISP data
        misp_results = misp_get(indicator)

        ## validated results
        if not misp_results:
            return "No Results for indicator {}".format(indicator)

        ## create slack messages and send
        for result in misp_results[0]:
            message = ""
            message += "```{} -> {}: {}```\n\n".format(indicator, result, misp_results[0][result])
            response = client.chat_postMessage(
                channel=channel, text=message, thread_ts=thread_ts
            )

        status = {"statusCode": 200, "body": "Done"}

        return status
    except Exception as e:
        client = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])
        response = client.chat_postMessage(channel=os.environ["SLACK_CHANNEL"], text=str(e))
        return "Error occurred, message sent to administrator"
