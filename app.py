import requests
from requests_oauthlib import OAuth1
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import settings
import json
import threading
import time
# import traceback


class XP_RPC():

    def __init__(self):
        self.connection = AuthServiceProxy(
            settings.RPC_URL % (settings.rpc_user, settings.rpc_password))
        self.tax = 1.0

    def get_address(self, name):
        # commands = [["getaddressesbyaccount", name]]
        address = self.connection.getaddressesbyaccount(name)
        if address:
            address = address[0]
        else:
            address = self.connection.getaccountaddress(name)
        return address

    def show_balance(self, name):
        address = self.connection.getaddressesbyaccount(name)
        if address:
            balance = self.connection.getbalance(name)
        else:
            address = self.connection.getaccountaddress(name)
            balance = self.connection.getbalance(name)
        print(balance)
        return balance

    def move_balance(self, name, to_name, amount):
        address = self.connection.getaddressesbyaccount(name)
        to_address = self.connection.getaddressesbyaccount(to_name)
        if address and to_address:
            # req = self.connection.move(name, to_name, amount)
            req = self.connection.move(name, to_name, amount)
        elif address:
            self.connection.getaccountaddress(to_name)
            req = self.connection.move(name, to_name, amount)
        else:
            req = "Error"
        return req

    def send_from(self, name, address, amount):
        txid = self.connection.sendfrom(name, address, amount)
        tx = self.connection.gettransaction(txid)
        if tx:
            fee = tx["fee"]
        else:
            fee = 0
        self.move_balance(name, "taxpot", float(fee) + self.tax)
        return txid

    def validateaddress(self, address):
        return self.connection.validateaddress(address)['isvalid']


class Twitter():

    def __init__(self):
        self.xpd = XP_RPC()
        self.auth_stream = OAuth1(settings.CONSUMER_KEY_STREAM, settings.CONSUMER_SECRET_STREAM,
                                  settings.ACCESS_TOKEN_STREAM, settings.ACCESS_TOKEN_SECRET_STREAM)
        self.auth_reply = OAuth1(settings.CONSUMER_KEY_REPLY, settings.CONSUMER_SECRET_REPLY,
                                 settings.ACCESS_TOKEN_REPLY, settings.ACCESS_TOKEN_SECRET_REPLY)
        self.tweets = []

    def reply(self, text, reply_token):
        params = {
            "status": text,
            "in_reply_to_status_id": reply_token,
            "auto_populate_reply_metadata": "true"
        }
        req = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json", auth=self.auth_reply, data=params)
        return req

    def detect(self, tweet):
        print("Detecting...")
        m = tweet["text"].split(" ")
        if m[0] == "@tip_XPchan":
            command = m[1]
            lang = tweet["user"]["lang"]
            address_name = "tipxpchan-" + tweet["user"]["id_str"]

            if command == "tip":
                print("tip in")
                amount = m[3]
                if m[2][0] == "@":
                    to_name = "tipxpchan-" + self.get_id(m[2][1:])
                    balance = self.xpd.show_balance(address_name)
                    amount = float(amount)
                    if balance >= amount:
                        if self.xpd.move_balance(address_name, to_name, amount):
                            if lang == "ja":
                                text = "XPちゃんより%sさんにお届けものだよっ！ %fXP\n『@￰tip_XPchan balance』で残高確認が行えるよ！" % (
                                    m[2], amount)
                            else:
                                text = "Present for %s! Sent %fXP!"
                            req = self.reply(text, tweet["id"])

                    else:
                        if lang == "ja":
                            text = "残高が足りないよ〜 所持XP:%f" % balance
                        else:
                            text = "Not enough balance! XP:%f" % balance
                        req = self.reply(text, tweet["id"])
                else:
                    print("エラーだよっ！よく確認してね！")

            elif command == "donate":
                print("donate in")
                amount = m[2]
                to_name = "tipxpchan-940589020509192193"
                balance = self.xpd.show_balance(address_name)
                amount = float(amount)
                if balance >= amount:
                    if self.xpd.move_balance(address_name, to_name, amount):
                        if lang == "ja":
                            text = "@%s 開発へのご支援ありがとうございます！" % tweet["user"]["name"]
                        else:
                            text = "@%s Thank you for donation！" % tweet["user"]["name"]
                        req = self.reply(text, tweet["id"])
                else:
                    if lang == "ja":
                        text = "残高が足りないよ〜 所持XP:%f" % balance
                    else:
                        text = "Not enough balance! XP:%f" % balance
                    req = self.reply(text, tweet["id"])

            elif command == "deposit":
                print("deposit in")
                if lang == "ja":
                    text = "%sさんのアドレスは「%s」だよっ！" % (
                        tweet["user"]["name"], self.xpd.get_address(address_name))
                else:
                    text = "%s 's address is 「%s」！" % (
                        tweet["user"]["name"], self.xpd.get_address(address_name))
                req = self.reply(text, tweet["id"])

            elif command == "withdraw":
                print("withdraw in")
                amount = m[3]
                balance = self.xpd.show_balance(address_name)
                amount = float(amount)
                address = m[2]
                if balance >= amount + self.xpd.tax:
                    if self.xpd.validateaddress(address):
                        txid = self.xpd.send_from(
                            address_name, address, amount)
                        if lang == "ja":
                            text = """
                            「%s」に%fXPを引き出したよ!(手数料:%dXP)\nhttps://chainz.cryptoid.info/xp/tx.dws?%s.htm
                            """ % (address, amount, self.xpd.tax, txid)
                        else:
                            text = """
                            Withdraw Complete! Sent %fXP to [%s]!(Fee:%dXP)\nhttps://chainz.cryptoid.info/xp/tx.dws?%s.htm
                            """ % (address, amount, txid)
                        req = self.reply(text, tweet["id"])
                    else:
                        if lang == "ja":
                            text = "ごめんなさい！アドレスが間違ってるみたいだよ！"
                        else:
                            text = "Invalid Address!"
                        req = self.reply(text, tweet["id"])
                else:
                    if lang == "ja":
                        text = "残高が足りないよ〜 所持XP:%f\n引き出しには手数料の%dXPがかかるよ!" % (
                            balance, self.xpd.tax)
                    else:
                        text = "Not enough balance! XP:%f\nPlease note that required %dXP fee when withdraw" % (
                            balance, self.xpd.tax)
                    req = self.reply(text, tweet["id"])

            elif command == "withdrawall":
                print("withdrawall in")
                balance = self.xpd.show_balance(address_name)
                amount = balance - self.xpd.tax
                address = m[2]
                if self.xpd.validateaddress(address):
                    txid = self.xpd.send_from(
                        address_name, address, amount)
                    if lang == "ja":
                        text = """
                        「%s」に%fXPを引き出したよ!(手数料:%dXP)\nhttps://chainz.cryptoid.info/xp/tx.dws?%s.htm
                        """ % (address, amount, self.xpd.tax, txid)
                    else:
                        text = """
                        Withdraw Complete! Sent %fXP to [%s]!(Fee:%dXP)\nhttps://chainz.cryptoid.info/xp/tx.dws?%s.htm
                        """ % (address, amount, self.xpd.tax, txid)
                    req = self.reply(text, tweet["id"])
                else:
                    if lang == "ja":
                        text = "ごめんなさい！アドレスが間違ってるみたいだよ！"
                    else:
                        text = "Invalid Address!"
                    req = self.reply(text, tweet["id"])

            elif command == "balance":
                print("balance in")
                if lang == "ja":
                    text = "%sさんの保有XPは%fXPだよん！" % (
                        tweet["user"]["name"], self.xpd.show_balance(address_name))
                else:
                    text = "%s 's balance is %fXP！" % (
                        tweet["user"]["name"], self.xpd.show_balance(address_name))
                req = self.reply(text, tweet["id"])

            else:
                print("command error")
                # text = "エラーだよっ！よく確認してね！"
                # req = self.reply(text, tweet["id"])

        else:
            pass

    def get_id(self, name):
        params = {
            "screen_name": name,
        }
        user_id = requests.get("https://api.twitter.com/1.1/users/show.json",
                               auth=self.auth_reply, params=params).json()["id_str"]
        return user_id


def collect():
    url = "https://stream.twitter.com/1.1/statuses/filter.json"
    # twitter = Twitter()
    # print(twitter.detect(tweet))
    _stream = requests.post(url, auth=twitter.auth_stream,
                            stream=True, data={"track": "@tip_XPchan"})
    for _line in _stream.iter_lines():
        try:
            _doc = json.loads(_line.decode("utf-8"))
            if _doc:
                twitter.tweets.append(_doc)
            else:
                pass
        except:
            print("エラー")
            pass


def job():
    while True:
        try:
            twitter.detect(twitter.tweets.pop(0))
            # print(twitter.tweets)
            time.sleep(5)
        except:
            time.sleep(1)
            # print(traceback.format_exc())
            continue


if __name__ == '__main__':
    twitter = Twitter()
    thread_1 = threading.Thread(target=collect)
    thread_2 = threading.Thread(target=job)

    thread_1.start()
    thread_2.start()
