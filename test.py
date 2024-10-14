import csv
from collections import defaultdict

def calculate_payouts(csv_file):
    playerNet = defaultdict(int)

    # Read and calculate net values for each player
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            playerID = row['player_id']
            net = int(row['net'])
            playerNet[playerID] += net

    # Optimize payouts
    payouts = optimize_payouts(playerNet)

    return payouts

def optimize_payouts(playerNet):
    
    creditors = [(player, net) for player, net in playerNet.items() if net > 0]
    debtors = [(player, net) for player, net in playerNet.items() if net < 0]

   
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1])

    payouts = {}

    
    while creditors and debtors:
        creditor, credit = creditors.pop(0)  
        debtor, debt = debtors.pop(0)        

        
        transaction_amount = min(credit, -debt)

    
        if creditor not in payouts:
            payouts[creditor] = {}
        payouts[creditor][debtor] = transaction_amount

       
        credit -= transaction_amount
        debt += transaction_amount

       
        if credit > 0:
            creditors.insert(0, (creditor, credit))
        if debt < 0:
            debtors.insert(0, (debtor, debt))

    return payouts

def get_player_nicknames(csv_file):
    player_map = {}
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            playerID = row['player_id']
            playerNickname = row['player_nickname']
            player_map[playerID] = playerNickname
    return player_map

def main():
    
    csv_file = input('Enter CSV File: ')
    payouts = calculate_payouts(csv_file)
    player_map = get_player_nicknames(csv_file)

    for posPlay, negPlays in payouts.items():
        posPlayNickname = player_map.get(posPlay, "unknown")
        print(f"{posPlayNickname} gets paid by:")
        for negPlay, amount in negPlays.items():
            new_amount = ((amount // 50) * 50) / 100
            negPlayNickname = player_map.get(negPlay, "unknown")
            print(f"  {negPlayNickname}: ${new_amount}0")

if __name__ == "__main__":
    main()
