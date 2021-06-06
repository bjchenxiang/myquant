import json
import requests
from loguru import logger
from datetime import datetime

def send_dingding_msg(content, robot_id=''):
    try:
        msg = {
            "msgtype": "text",
            "text": {"content": content + '\n\n' + datetime.now().strftime("%m-%d %H:%M:%S")}}
        headers = {"Content-Type": "application/json;charset=utf-8"}
        url = 'https://oapi.dingtalk.com/robot/send?access_token=' + robot_id                
        body = json.dumps(msg)
        requests.post(url, data=body, headers=headers)
        print('成功发送钉钉')
    except Exception as e:
        print("发送钉钉失败:", e)


def print_trade_analysis(analyzer):
    # Get the results we are interested in
    if not analyzer.get("total"):
        return

    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total, 2)
    strike_rate = round((total_won / total_closed) * 2)

    # Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
    r1 = [total_open, total_closed, total_won, total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]

    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)

    # Print the rows
    print_list = [h1, r1, h2, r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('', *row))


def print_sqn(analyzer):
    sqn = round(analyzer.sqn, 2)
    print('SQN: {}'.format(sqn))


if __name__ == '__main__':
    print('ok')
    send_dingding_msg('交易提醒：\n\rtest', robot_id='5976356a909a8bdddba07bb0132f17507b9cf8483e1ff1e0702fbbe534ea60b0')