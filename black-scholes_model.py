import math
from scipy.stats import norm

#Volatility Input
while True:
    volatility = float(input("Volatility/Alpha (decimal): "))
    if(volatility < 0):
        print("Volatility cannot be a negative value, please enter a correct value.")
    else:
        break

#Current Price Input
while True:
    current_price = float(input("Current Share Price: "))
    if(current_price < 0):
        print("Current Share Price cannot be a negative value, please enter a correct value.")
        current_price = float(input("Current Share Price: "))
    else:
        break

#Strike Price Input
while True:
    strike_price = float(input("Strike Price: "))
    if(strike_price < 0):
        print("Strike Price cannot be a negative value, please enter a correct value.")
        strike_price = float(input("Strike Price: "))
    else:
        break

#Interest rate Input
interest_rate = float(input("Interest rate (percent): "))

#Maturity Input
while True:
    maturity = float(input("Maturity (years): "))
    if(maturity < 0):
        print("Maturity cannot be a negative value, please enter a correct value.")
        maturity = float(input("Maturity (years): "))
    else:
        break

#Calculation

#d1
d1 = (math.log(current_price / strike_price) + (math.log1p(interest_rate) + math.pow(volatility, 2)/2 * maturity))/(volatility * math.sqrt(maturity))

#d2
d2 = d1 - volatility * math.sqrt(maturity)

#black-scholes-formula
price = current_price * math.n
