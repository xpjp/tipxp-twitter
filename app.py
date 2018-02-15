import requests
from requests_oauthlib import OAuth1
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import settings
import json
import threading
import time
import mysql.connector
import traceback
import re

from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


class XP_RPC():

    def __init__(self):
        self.connection = AuthServiceProxy(
            settings.RPC_URL % (settings.rpc_user, settings.rpc_password))
        self.tax = 1.0

    def get_address(self, name):
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
        self.conn = mysql.connector.connect(
            user=settings.dbuser, password=settings.dbpass, host=settings.dbhost, database=settings.dbname)
        self.cur = self.conn.cursor()

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
        pattern = r"RT\s(.*)"
        m = re.search(pattern, tweet["text"])
        if tweet["text"][0:2] != "RT":
            pattern = r"@tip_XPchan\s((?:d(?:eposit|onate)|withdraw(?:all)?|balance|tip))\s?(.*)"
            m = re.search(pattern, tweet["text"])
            if m:
                logger.debug(m.group(0))
                command = m.group(1)
                lang = tweet["user"]["lang"]
                address_name = "tipxpchan-" + tweet["user"]["id_str"]

                if command == "tip":
                    print("tip in")
                    pattern = r"(@.*)\s([0-9]+\.?[0-9]*)\s?(.*)"
                    m = re.search(pattern, m.group(2))
                    if m:
                        amount = m.group(2)
                        to_name, lang = self.get_id(m.group(1)[1:])
                        to_name = "tipxpchan-" + to_name
                        balance = self.xpd.show_balance(address_name)
                        amount = float(amount)
                        if balance >= amount:
                            if self.xpd.move_balance(address_name, to_name, amount):
                                if lang == "ja":
                                    text = "XPちゃんより%sさんにお届けものだよっ！ %fXP\n『@￰tip_XPchan balance』で残高確認が行えるよ！" % (
                                        m.group(1), amount)
                                else:
                                    text = "Present for %s! Sent %fXP!" % (
                                        m.group(1), amount)
                                try:
                                    if "#XPちゃんねる" in m.group(3):
                                        service = "xpchannnel"
                                    elif "#XPのべる" in m.group(3):
                                        service = "xpnovel"
                                    else:
                                        service = "twitter"
                                    self.cur.execute("insert into tip_history (tipfrom, tipto, amount, service) values (%s, %s, %s, %s)", (
                                        tweet["user"]["screen_name"], m.group(1)[1:], amount, service))
                                    self.conn.commit()
                                    req = self.reply(text, tweet["id"])
                                except:
                                    print(traceback.format_exc())
                                    req = self.reply(text, tweet["id"])

                        else:
                            if lang == "ja":
                                text = "残高が足りないよ〜 所持XP:%f" % balance
                            else:
                                text = "Not enough balance! XP:%f" % balance
                            req = self.reply(text, tweet["id"])
                    else:
                        print("構文エラー")

                elif command == "donate":
                    print("donate in")
                    pattern = r"([0-9]+\.?[0-9]*)\s?.*"
                    m = re.search(pattern, m.group(2))
                    if m:
                        amount = m.group(1)
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
                    pattern = r"(\w*)\s?([0-9]+\.?[0-9]*)\s?.*"
                    m = re.search(pattern, m.group(2))
                    if m:
                        amount = m.group(2)
                        balance = self.xpd.show_balance(address_name)
                        amount = float(amount)
                        address = m.group(1)
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
                    pattern = r"(\w*)\s?.*"
                    m = re.search(pattern, m.group(2))
                    if m:
                        balance = self.xpd.show_balance(address_name)
                        amount = float(balance) - self.xpd.tax
                        address = m.group(1)
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
        res = requests.get("https://api.twitter.com/1.1/users/show.json",
                               auth=self.auth_reply, params=params).json()
        user_id = res["id_str"]
        lang = res["lang"]
        return user_id, lang


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
            # print("エラー")
            pass


def job():
    while True:
        try:
            twitter.detect(twitter.tweets.pop(0))
            # print(twitter.tweets)
            time.sleep(30)
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
