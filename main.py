import discord
from discord.ext import commands
import requests
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
print(f"TOKEN: {TOKEN}")

intents = discord.Intents.default()  
intents.message_content = True    
intents.members = True   

bot = commands.Bot(command_prefix="!", intents=intents)


def fetch_data(url, headers=None):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        return response.json()
    except requests.RequestException as e:
        return f"Error fetching data: {e}"


def calculate_payouts(data):
    playerNet = defaultdict(int)

    for playerID, playerInfo in data['playersInfos'].items():
        net = int(playerInfo['net'])
        playerNickname = playerInfo['names'][0].lower() 
        
        if playerNickname in ['sid', 'sid mobile :(']:
            playerID = 'sid_combined'
        if playerNickname in ['aadrij', 'Aadrij']:
            playerID = 'aadrij_combined'
        if playerNickname in ['aarav jai', 'aarav j']:
            playerID = 'aarav_combined'
                
        playerNet[playerID] += net  

    return optimize_payouts(playerNet)


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

def get_player_nicknames(data):
    player_map = {}
    
    for playerID, playerInfo in data['playersInfos'].items():
        playerNickname = playerInfo['names'][0]  
        
        if playerNickname.lower() in ['sid', 'sid mobile :(']:
            player_map['sid_combined'] = 'sid'
        elif playerNickname.lower() in ['aadrij', 'Aadrij']:
            player_map['aadrij_combined'] = 'aadrij'
        elif playerNickname.lower() in ['aarav j', 'aarav jai']:
            player_map['aarav_combined'] = 'aarav'
        else:
            player_map[playerID] = playerNickname
                
    return player_map


@bot.command(name='ledger')
async def ledger(ctx, game_url: str):
    poker_now_url = f"{game_url.rstrip('/')}/players_sessions"

    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",        
    }

    data = fetch_data(poker_now_url, headers=headers)

    if data:
        payouts = calculate_payouts(data)
        player_map = get_player_nicknames(data)
        members = {member.display_name.lower(): member for member in ctx.guild.members}
        
        result = []
        
        for posPlay, negPlays in payouts.items():
            posPlayNickname = player_map.get(posPlay, "unknown")
            posPlayMention = members.get(posPlayNickname.lower(), posPlayNickname)
            
            if isinstance(posPlayMention, discord.Member):
                posPlayMention = posPlayMention.mention
            result.append(f"**{posPlayMention}** gets paid by:") 
            for negPlay, amount in negPlays.items():
                negPlayNickname = player_map.get(negPlay, "unknown")
                negPlayMention = members.get(negPlayNickname.lower(), negPlayNickname)
                if isinstance(negPlayMention, discord.Member):
                    negPlayMention = negPlayMention.mention
                
                
                new_amount = ((amount // 50) * 50)/100
                result.append(f"{negPlayMention}: ${new_amount}0")  
            result.append("")
            
                
        await ctx.send("\n".join(result))
    else:
        await ctx.send("Failed to fetch game data.")

bot.run(TOKEN)
