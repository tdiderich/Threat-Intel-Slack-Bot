import requests
import slack
import os

SLACK_TOKEN = os.environ["SLACK_API_TOKEN"]
SLACK_CHANNEL = os.environ["SLACK_CHANNEL"]

jask_api_key = os.environ["JASK_API_KEY"]
jask_base_url = os.environ["JASK_BASE_URL"]


def jask_insight_get(uid):
    path = "/api/v1/insights/{}".format(uid)
    url = jask_base_url + path

    jask_results = requests.get(url, headers={'X-API-KEY': jask_api_key}).json()
    return jask_results


def handler(event, context):
    try:
        channel = event['body']['channel_id']
        uid = event['body']['text']
        if not uid:
            return "Please enter an input"

        ## first message to start thread + avoid timeout
        client = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])
        bot_message = '```Link to Insight: {}/insight/{}```'.format(jask_base_url, uid)
        response = client.chat_postMessage(channel=channel, text=bot_message)
        thread_ts = response["ts"]

        ## get JASK Insight results
        jask_results = jask_insight_get(uid)

        if not jask_results:
            return "No Results for uid {}".format(uid)

        # set count for signals loop
        count = 0
        for result in jask_results['data']:
            if result == 'signals':
                while (count < len(jask_results['data']['signals'])):
                    message = ""
                    message += "```Signal {}: {}```\n\n".format(count+1, jask_results['data']['signals'][count])
                    count += 1
                    response = client.chat_postMessage(
                        channel=channel, text=message, thread_ts=thread_ts
                    )
            else:
                message = ""
                message += "```{}: {}```\n\n".format(result, jask_results['data'][result])

            response = client.chat_postMessage(
                channel=channel, text=message, thread_ts=thread_ts
            )

        status = {"statusCode": 200, "body": "Done"}

        return status
    except Exception as e:
        client = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])
        response = client.chat_postMessage(channel=SLACK_CHANNEL, text=str(e))
        return "Error occurred, message sent to administrator"
