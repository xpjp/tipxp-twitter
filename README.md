# tipxp-twitter
Twitter用XPチップBot

## 使い方
settings.pyを作成し、必要な情報を書き込む
```
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
RPC_URL = ""
rpc_user = ""
rpc_password = ""
```

## コマンド一覧

- tip
```
@tip_XPchan tip @[アカウント] [数量]
```
指定したTwitterアカウントあてにXPを送る

- balance
```
@tip_XPchan balance
```
Twitterアカウントに紐づいたアドレスの残高を表示する

- deposit
```
@tip_XPchan deposit
```
Twitterアカウントに紐づいたアドレスを表示する

- withdraw(未実装)
```
@tip_XPchan withdraw [アドレス] [数量]
```
XPアドレスに数量分のXPを送金する

- withdrawall(未実装)
```
@tip_XPchan withdrawall [アドレス]
```
XPアドレスに全額XPを送金する
