import datetime
import json
import requests
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .forms import CryptoForm, DepositForm
from wallets.models import CustomUser, Transaction, Coin
from django.core.cache import cache

# Create your views here.
class HomePageView(TemplateView):
    template_name = 'home.html'

def home_view(request): # -> Dashboard Tab
    api_data_view = cache.get('api_data_view')
    if api_data_view is None:
        api_data_view = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false').json()
        # caching the fetched data for 1 minute
        cache.set('api_data_view', api_data_view, 60)
    return render(request, 'home.html', {'api_data': api_data_view})

def deposit_view(request): # -> Deposit Tab
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            value = form.cleaned_data['value']
            user = request.user
            user.total_deposits_usd += value
            user.current_holdings_dollars += value
            user.save()
        return redirect('success_deposit_view', value=value)

    else:
        form = DepositForm()
        return render(request, 'deposit.html', {'form' : form})

def success_deposit_view(request, value): # -> Deposit/Success Tab
    return render(request, 'success_deposit.html', {'value' : value})

def trade_view(request):
    # last year data
    api_data_year = cache.get('api_data_year')
    if api_data_year is None:
        api_data_year = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily').json()
        # caching the fetched data for 1 minute
        cache.set('api_data_year', api_data_year, 60)
    year_data = []
    for item in api_data_year['prices']:
        year_data.append(item[1])

    # last month data
    api_data_month = cache.get('api_data_month')
    if api_data_month is None:
        api_data_month = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30&interval=daily').json()
        # caching the fetched data for 1 minute
        cache.set('api_data_month', api_data_month, 60)
    month_data = []
    for item in api_data_month['prices']:
        month_data.append(item[1])

    # last week data
    api_data_week = cache.get('api_data_week')
    if api_data_week is None:
        api_data_week = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7&interval=hourly').json()
        # caching the fetched data for 1 minute
        cache.set('api_data_week', api_data_week, 60)
    week_data = []
    for item in api_data_week['prices']:
        week_data.append(item[1])

    # last day data
    api_data_day = cache.get('api_data_day')
    if api_data_day is None:
        api_data_day = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1&interval=hourly').json()
        # caching the fetched data for 1 minute
        cache.set('api_data_day', api_data_day, 60)
    day_data = []
    for item in api_data_day['prices']:
        day_data.append(item[1])

    data = {
        'year_data' : year_data,
        'month_data' : month_data,
        'week_data' : week_data,
        'day_data' : day_data,
    }
    return render(request, 'trade.html', {'data' : data})

def buy_view(request):
    if request.method == 'POST':
        form = CryptoForm(request.POST)
        if form.is_valid():
            user = request.user
            crypto = form.cleaned_data['crypto'].lower()
            quantity = form.cleaned_data['quantity']
            api_data_buy = requests.get(f'https://api.coingecko.com/api/v3/coins/{crypto}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false').json()
            coin_current_price = api_data_buy['market_data']['current_price']['usd']
            needed_dollars = quantity * coin_current_price
            # check if we have the needed funds
            if needed_dollars < user.current_holdings_dollars: # current_account_value = dollars
                user.current_holdings_dollars = user.current_holdings_dollars - needed_dollars
                user.current_holdings_crypto += needed_dollars
                user.save()
                # if coin exists in user's wallet, we change the quantity attribute
                if user.coins.filter(name=crypto).exists(): # if coin exists
                    coin = user.coins.filter(name=crypto).first()
                    coin.average_price = ((coin.quantity * coin.average_price) + (quantity * coin_current_price)) / (coin.quantity + quantity)
                    coin.quantity += quantity
                    coin.last_recorded_price = coin_current_price
                    coin.save()
                # if coin doesn't exist in user's wallet, we create it
                else:
                    coin = Coin.objects.create(name=crypto, quantity=quantity, last_recorded_price=coin_current_price, average_price=coin_current_price)
                    user.coins.add(coin)
                # create transaction
                transaction = Transaction.objects.create(type="Buy transaction", date=datetime.datetime.now(), coin_name=crypto, quantity=quantity, price_when_bought=coin_current_price)
                user.transactions.add(transaction)
                return redirect('success_buy_view', crypto=crypto)
            else:
                return redirect('error_buy_view', crypto=crypto)
    else:
        form = CryptoForm()
        return render(request, 'buy.html', {'form' : form})

def success_buy_view(request, crypto):
    return render(request, 'success_buy.html', {'crypto' : crypto})

def error_buy_view(request, crypto):
    return render(request, 'error_buy.html', {'crypto' : crypto})

def sell_view(request):
    if request.method == 'POST':
        form = CryptoForm(request.POST)
        if form.is_valid():
            user = request.user
            crypto = form.cleaned_data['crypto'].lower()
            quantity = form.cleaned_data['quantity']
            api_data_sell = requests.get(f'https://api.coingecko.com/api/v3/coins/{crypto}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false').json()
            coin_current_price = api_data_sell['market_data']['current_price']['usd']
            # check if the current user has the crypto coin in his wallet
            if user.coins.filter(name=crypto).exists():
                found_coin_in_database = user.coins.filter(name=crypto).first()
                # check if we have the needed quantity to sell
                if found_coin_in_database.quantity >= quantity:
                    # sell the coin
                    user.current_holdings_dollars += quantity * coin_current_price
                    user.current_holdings_crypto -= quantity * coin_current_price
                    user.save()
                    found_coin_in_database.quantity -= quantity
                    found_coin_in_database.last_recorded_price = coin_current_price
                    found_coin_in_database.save()
                    transaction = Transaction.objects.create(type="Sell transaction", date=datetime.datetime.now(), coin_name=crypto, quantity=quantity, price_when_bought=coin_current_price)
                    user.transactions.add(transaction)
                    return redirect('success_sell_view', crypto=crypto)
                else:
                    return redirect('error_sell_view', crypto=crypto)
            else:
                return redirect('error_sell_view', crypto=crypto)
        else:
            return redirect('error_sell_view', crypto=crypto)

    else:
        form = CryptoForm()
        return render(request, 'sell.html', {'form' : form})

def success_sell_view(request, crypto):
    return render(request, 'success_sell.html', {'crypto' : crypto})

def error_sell_view(request, crypto):
    return render(request, 'error_sell.html', {'crypto' : crypto})

def portfolio_view(request):
    user = request.user
    username = user.username
    email = user.email
    total_deposited_usd = user.total_deposits_usd

    coins = user.coins.all()
    current_total_balance_wallet = 0
    names = []
    prices = []
    quantities = []

    api_data_portfolio = cache.get('api_data_portfolio')
    if api_data_portfolio is None:
        # calculate current total balance of wallet(crypto + usd)
        for coin in coins:
            name = coin.name
            quantity = coin.quantity
            # fetch information about coin price
            request_data = requests.get(f'https://api.coingecko.com/api/v3/coins/{name}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false').json()
            price = request_data['market_data']['current_price']['usd']
            names.append(name)
            prices.append(price*quantity)
            quantities.append(quantity)
            current_total_balance_wallet += (price*quantity)

        api_data_portfolio = {
            'prices' : prices,
            'names' : names,
            #'quantities' : quantities
        }
        # caching the fetched data for 20 seconds
        cache.set('api_data_portfolio', api_data_portfolio, 20)
    prices = api_data_portfolio['prices']
    names = api_data_portfolio['names']
    # add prices from cache to calculate current total balance of wallet
    for price in prices:
        current_total_balance_wallet += price
    current_total_balance_wallet += user.current_holdings_dollars
    # add the usd holdings
    names.append('usd')
    prices.append(user.current_holdings_dollars)
    quantities.append(user.current_holdings_dollars)

    if total_deposited_usd != 0:
        percentage = ((current_total_balance_wallet - total_deposited_usd) / total_deposited_usd)*100
        percentage = f"{percentage:.3f}"
    else:
        percentage = 0.000
    current_dollars = user.current_holdings_dollars
    data = {
        'username' : username,
        'email' : email,
        'total_deposited_usd' : total_deposited_usd,
        'current_dollars' : f"{current_dollars:.3f}",
        'coins' : coins,
        'current_total_balance_wallet' : current_total_balance_wallet,
        'percentage' : percentage,
        'prices' : prices,
        'names' : names,
        #'quantities' : quantities
    }

    return render(request, 'portfolio.html', {'data': data})

def transactions_view(request):
    user = request.user
    transactions = user.transactions.all()

    return render(request, 'transactions.html', {'transactions': transactions})



