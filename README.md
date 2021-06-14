# Instagram cat liker bot

This bot is make to automaticolly like cat images on Istagram. Cat are reconized by a pre trained neural network. 

## Instalation

This project use Pipenv as a virtual environement. You can install Pipenv by following this [link](https://pipenv.pypa.io/en/latest/install/)

Once Pipenv is installed, create a virtual env with Python 3 with this command
> pipenv --three

To install third package, run this command
> pipenv install

## Environement

Set you env with a `.env` file like followed:

```
INSTA_USERNAME=
INSTA_PASSWORD=
DISCORD_WEBHOOK_URL=
SENTRY_SDK_URL=
ENVIRONMENT=
```

### Notification

Liked/detected images are sended on Discord via a webhook.

You can create a webhook by following this [link](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

### Sentry

A sentry sdk url and environement variable are required to track exceptions.

## Run

To run the bot:

> pipenv run python like_cat.py

or by cron

> */5 7-22 * * * cd your/path && pipenv run python like_bot.py --min_loc 12 --max_loc 16
> */5 7-22 * * * cd your/path && pipenv run python like_bot.py -f --min_loc 12 --max_loc 16