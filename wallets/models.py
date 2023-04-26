from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Coin(models.Model):
    name = models.CharField(max_length=32)
    last_recorded_price = models.FloatField() # current_price = models.FloatField() 
    average_price = models.FloatField() 
    quantity = models.FloatField(default=0.0)

class Transaction(models.Model):
    type = models.CharField(max_length=32)
    date = models.DateTimeField()
    coin_name = models.CharField(max_length=32)
    quantity = models.FloatField()
    price_when_bought = models.FloatField()

    def __str__(self):
        return self.coin_name

class CustomUser(AbstractUser):
    total_deposits_usd = models.IntegerField(default = 0) 
    current_holdings_dollars = models.FloatField(default=0.0) # current_account_value = models.FloatField(default=0.0) 
    current_holdings_crypto = models.FloatField(default=0.0) # cryptocurrencies_value = models.FloatField(default=0.0) 
    coins = models.ManyToManyField(Coin)
    transactions = models.ManyToManyField(Transaction)

    def __str__(self): 
        return self.email 