import discord
from discord.ext import commands
import requests
from collections import defaultdict


intents = discord.Intents.default()  
intents.message_content = True       

bot = commands.Bot(command_prefix="!", intents=intents)


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.json()
    except requests.RequestException as e:
        return f"Error fetching data: {e}"

# Calculate payouts based on the player data
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
    
    posPlays = {}
    negPlays = {}
    
    for player, net in playerNet.items():
        if net > 0:
            posPlays[player] = net
        elif net < 0:
            negPlays[player] = net
    
    payouts = {}
    for posPlay, positive_net in posPlays.items():
        payouts[posPlay] = {}
        remaining_net = positive_net
        for negPlay, negative_net in sorted(negPlays.items(), key=lambda x: x[1]):
            if remaining_net == 0:
                break
            if abs(negative_net) >= remaining_net:
                payouts[posPlay][negPlay] = remaining_net
                negPlays[negPlay] += remaining_net
                remaining_net = 0
            else:
                payouts[posPlay][negPlay] = abs(negative_net)
                remaining_net -= abs(negative_net)
                negPlays[negPlay] += abs(negative_net)
        negPlays = {k: v for k, v in negPlays.items() if v < 0}
    
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

    data = fetch_data(poker_now_url)

    if data:
        payouts = calculate_payouts(data)
        player_map = get_player_nicknames(data)
        
        result = []
        
        for posPlay, negPlays in payouts.items():
            posPlayNickname = player_map.get(posPlay, "unknown")
            result.append(f"**{posPlayNickname}** gets paid by:") 
            
            for negPlay, amount in negPlays.items():
                negPlayNickname = player_map.get(negPlay, "unknown")
                result.append(f"{negPlayNickname}: {amount}")  
            
            result.append("")  

        await ctx.send("\n".join(result))
    else:
        await ctx.send("Failed to fetch game data.")


bot.run('MTI5Mjc2NTU1MDI1ODI5MDcwOA.G0qcYf.z0YhAxLQsDwbCV71A8vhEXYp3d__HRzSfSuIGc')
