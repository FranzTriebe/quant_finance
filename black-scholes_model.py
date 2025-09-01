
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
    current_price = float(input("Strike Price: "))
    if(current_price < 0):
        print("Strike Price cannot be a negative value, please enter a correct value.")
        current_price = float(input("Strike Price: "))
    else:
        break

#Interest rate Input
current_price = float(input("Interest rate (percent): "))

#Maturity Input
while True:
    current_price = float(input("Maturity (years): "))
    if(current_price < 0):
        print("Maturity cannot be a negative value, please enter a correct value.")
        current_price = float(input("Maturity (years): "))
    else:
        break

