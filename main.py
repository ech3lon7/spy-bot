import yfinance as yf
import requests
import os # We use this to grab the secret password from GitHub

# --- CONFIGURATION ---
# We get the URL from GitHub's "Secrets" vault for safety
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print(">> No Webhook found. Check GitHub Secrets.")
        return
    
    data = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
        print(">> Discord Alert Sent!")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

def run_analysis():
    print(f"--- Fetching Data ---")
    
    spy = yf.Ticker("SPY")
    df = spy.history(period="1mo") 
    
    if df.empty:
        print("Error: Could not fetch data.")
        return

    today = df.iloc[-1]
    history = df.iloc[:-1]
    
    avg_range = (history['High'] - history['Low']).tail(10).mean()
    today_tr = today['High'] - today['Low']
    
    range_span = today_tr if today_tr > 0 else 1.0
    cl_score = (today['Close'] - today['Low']) / range_span

    # Regime
    regime = "Normal"
    if today_tr >= (1.3 * avg_range): regime = "Expansion"
    elif today_tr <= (0.7 * avg_range): regime = "Compression"

    # Location
    loc = "Middle"
    if cl_score >= 0.8: loc = "Near High"
    elif cl_score <= 0.2: loc = "Near Low"

    # Structure
    structure = "SKIP / UNSURE"
    if regime == 'Expansion': structure = "IRON CONDOR"
    elif regime == 'Compression':
        structure = "BULL PUT SPREAD" if loc == 'Near High' else ("BEAR CALL SPREAD" if loc == 'Near Low' else "SKIP")
    elif regime == 'Normal':
        structure = "PUT SPREAD" if loc == 'Near High' else ("CALL SPREAD" if loc == 'Near Low' else "IRON CONDOR")

    msg = f"""**🚨 SPY 3:55 PM ALERT**
**Price:** ${today['Close']:.2f}
**Setup:** {regime} + {loc}
**👉 PLAY:** {structure}"""
    
    send_discord_alert(msg)

if __name__ == "__main__":
    run_analysis()