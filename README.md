# tipxp-twitter
Twitter用XPチップBot

# 目次(TOC)
- [Usage](#使い方)
- [コマンド一覧](#コマンド一覧)
- [CommandList](#commandlist)

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
@tip_XPchan tip @[ユーザー名] [数量]
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

- donate
```
@tip_XPchan donate [数量]
```
開発者に支援XPを送る

- withdraw
```
@tip_XPchan withdraw [アドレス] [数量]
```
XPアドレスに数量分のXPを送金する

- withdrawall
```
@tip_XPchan withdrawall [アドレス]
```
XPアドレスに全額XPを送金する

## CommandList

- tip
```
@tip_XPchan tip @[UserName] [Amount]
```
Send XP to TwitterUser

- balance
```
@tip_XPchan balance
```
Show Balance

- deposit
```
@tip_XPchan deposit
```
Show Address

- donate
```
@tip_XPchan donate [Amount]
```
Donate for developers

- withdraw
```
@tip_XPchan withdraw [Address] [Amount]
```
Send an amount of XP to address

- withdrawall
```
@tip_XPchan withdrawall [Address]
```
Send your full amount XP to address
