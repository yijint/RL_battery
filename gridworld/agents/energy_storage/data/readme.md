## Data sources
Load: gridstatus
Load forecast: gridstatus
Historical Locational Marginal Pricing: gridstatus
MOER (2017.01-2024.10): https://content.sgipsignal.com/download-data/ 
SOC: built-in (gridworld)
Price forecast: forecasting method is an active area of research (see https://github.com/Morgan-Sell/caiso-price-forecast for a summary of methods), many RL methods assume a perfect forecast by just indexing future prices. Of all existing methods, LSTM tends to perform the best (see https://github.com/Morgan-Sell/caiso-price-forecast). Implement this as a stretch goal,

### MOER 
#### Characteristics of Each DLAP Region
- SDG&E DLAP: San Diego has relatively high solar penetration, leading to significant midday dips in MOER due to solar generation. Evening ramp-ups can also lead to higher MOER due to natural gas peakers.
- PG&E DLAP: PG&E has a mix of hydropower, nuclear (Diablo Canyon), and solar. Marginal emissions might be lower due to cleaner baseload resources.
- SCE DLAP: SCE serves a large area with diverse energy sources but often relies heavily on natural gas during peak hours. Its MOER could show a more consistent higher baseline compared to SDG&E.
#### Choice of DLAP Region for training a price-taking battery agent 
A portion of the SDG&E DLPA will be used for training with the remaining portion reserved for testing. 

### Future directions
- Domain shift: how does model performance generalize to MOER from different DLAP regions and energy prices from different locations?
- Implementing price forecast (see https://github.com/Morgan-Sell/caiso-price-forecast)