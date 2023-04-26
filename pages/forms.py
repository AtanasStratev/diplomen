from django import forms
import requests

class CryptoForm(forms.Form):
    api_data = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false').json()
    CRYPTO_CHOICES = []
    for item in api_data:
        CRYPTO_CHOICES.append((item['id'], item['id']))


    crypto = forms.ChoiceField(choices=CRYPTO_CHOICES)
    quantity = forms.FloatField() # new, was decimal


class DepositForm(forms.Form):
    value = forms.IntegerField() # new, was decimal
    currency = 'USD'