# hackathon_relaxdays_market_simulation

# Market-Simulation

## Problem Description

Winning solution for the market-simulation competition from the third Relaxdays Hackathon.

There is a market simulation for buying and listing stocks. 

The market has suppliers, which list stocks with random prices. 
The competiting players can then buy those stocks to this prices and list them for higher prices again. 

Player do not buy from other players, 

but all players can buy from all suppliers 
and all suppliers buy from all players.

## Solution

Time was were short. The basic solution was to accept the randomness of the market. 

I assumend all articles are somehow in equal price intervals. 

1. Wait and analyse market for 20 iterations of new supplier price information
2. Start with buying all items with prices below 0.01-quantil and list them at the 0.45-quantil for low Time-To-Sold and maximum growth.
3. Raise those quantils with earning money (e.g. with 10,000, quantils go to 0.1 and 0.55)

