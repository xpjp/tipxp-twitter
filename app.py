# import twitter
import requests
from requests_oauthlib import OAuth1
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import settings
import json

auth = OAuth1(settings.CONSUMER_KEY, settings.CONSUMER_SECRET,
              settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)


class XP_RPC():

    def __init__(self):
        self.connection = AuthServiceProxy(
            settings.RPC_URL % (settings.rpc_user, settings.rpc_password))

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


class Twitter():

    def __init__(self):
        self.xpd = XP_RPC()
        self.auth = OAuth1(settings.CONSUMER_KEY, settings.CONSUMER_SECRET,
                           settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)

    def reply(self, text, reply_token):
        params = {
            "status": text,
            "in_reply_to_status_id": reply_token,
            "auto_populate_reply_metadata": "true"
        }
        req = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json", auth=self.auth, data=params)
        return req

    def detect(self, tweet):
        print("Detecting...")
        m = tweet["text"].split(" ")
        if m[0] == "@tip_XPchan":
            command = m[1]
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
                            text = """
                            XPちゃんより%sさんにお届けものだよっ！ %fXP\n『@￰tip_XPchan balance』で受取と残高確認が行えるよ！
                            """ % (m[2], amount)
                            req = self.reply(text, tweet["id"])
                    else:
                        text = "残高が足りないよ〜 所持XP:%f" % balance
                        req = self.reply(text, tweet["id"])
                else:
                    print("エラーだよっ！よく確認してね！")

            elif command == "deposit":
                print("deposit in")
                text = "%sさんのアドレスは「%s」だよっ！" % (
                    tweet["user"]["name"], self.xpd.get_address(address_name))
                req = self.reply(text, tweet["id"])

            elif command == "withdraw":
                pass

            elif command == "withdrawall":
                print("withdrawall in")
                if m[2][0] == "@":
                    to_name = "tipxpchan-" + self.get_id(m[2][1:])
                    balance = self.xpd.show_balance(address_name)
                    if balance >= float(amount):
                        self.xpd.move_balance(address_name, to_name, amount)
                    else:
                        text = "残高が足りないよ〜 所持XP:%f" % balance
                        req = self.reply(text, tweet["id"])

                else:
                    text = "エラーだよっ！よく確認してね！"
                    req = self.reply(text, tweet["id"])

            elif command == "balance":
                print("balance in")
                text = "%sさんの保有XPは%fXPだよん！" % (
                    tweet["user"]["name"], self.xpd.show_balance(address_name))
                req = self.reply(text, tweet["id"])

            else:
                print("command error")
                text = "エラーだよっ！よく確認してね！"
                req = self.reply(text, tweet["id"])

        else:
            pass

    def get_id(self, name):
        params = {
            "screen_name": name,
        }
        user_id = requests.get("https://api.twitter.com/1.1/users/show.json", auth=self.auth, params=params).json()["id_str"]
        return user_id


def main():
    url = "https://stream.twitter.com/1.1/statuses/filter.json"
    twitter = Twitter()
    # print(twitter.detect(tweet))
    _stream = requests.post(url, auth=twitter.auth, stream=True, data={"track":"@tip_XPchan"})
    for _line in _stream.iter_lines():
        try:
            _doc = json.loads(_line.decode("utf-8"))
            print(_doc)
            print(twitter.detect(_doc))
        except:
            print("エラー")
            pass


if __name__ == '__main__':
    main()
