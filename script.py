import time
from datetime import datetime
from nsetools import Nse
import warnings
warnings.filterwarnings('ignore')

def get_strongest_gainer():
    nse = Nse()
    
    try:
        # Get all top gainers
        gainers = nse.get_top_gainers(index='ALL')
        
        if not gainers:
            print("No gainers data available")
            return None
        
        # Find stock with best combination of factors
        best_stock = None
        best_score = -999
        
        for stock in gainers:
            try:
                # Calculate a composite score
                score = 0
                
                # Higher percentage change is better
                score += float(stock.get('net_price', stock.get('perChange', 0))) * 2
                
                # Higher volume gives more confidence
                vol_score = min(float(stock.get('trade_quantity', 0)) / 100000, 10)
                score += vol_score
                
                # Higher turnover is better
                turnover = float(stock.get('turnover', stock.get('turnoverInLakhs', 0)))
                turnover_score = min(turnover / 100, 5)
                score += turnover_score
                
                # Check if it's making new highs (approximate check)
                if stock.get('prev_price', 0) and stock.get('ltp', 0):
                    if float(stock['ltp']) > float(stock['prev_price']) * 1.1:
                        score += 5
                




                # Check for gap up opening
                if stock.get('open_price', 0) and stock.get('prev_price', 0):
                    gap_up = (float(stock['open_price']) - float(stock['prev_price'])) / float(stock['prev_price']) * 100
                    if gap_up > 5:
                        score += 10
                    elif gap_up > 3:
                        score += 5
                
                # Check if trading near day's high
                if stock.get('high_price', 0) and stock.get('ltp', 0):
                    proximity_to_high = (float(stock['high_price']) - float(stock['ltp'])) / float(stock['high_price']) * 100
                    if proximity_to_high < 2:
                        score += 10
                    elif proximity_to_high < 5:
                        score += 5

                # Add extra points if similar to pattern (12-18% gain at 9:35)
                net_price = float(stock.get('net_price', stock.get('perChange', 0)))
                if 12 <= net_price <= 18:
                    score += 15  # Bonus for perfect pattern match




                if score > best_score:
                    best_score = score
                    best_stock = stock
                    
            except Exception as e:
                continue
        
        if best_stock:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"Time: {current_time}")

            print(f"Stock: {best_stock['symbol']}")
            print(f"Price: ₹{best_stock['ltp']}")
            print(f"Change: {best_stock.get('net_price', best_stock.get('perChange', 'N/A'))}%")
            print(f"Open: ₹{best_stock.get('open_price', 'N/A')}")
            print(f"High: ₹{best_stock.get('high_price', 'N/A')}")
            print(f"Volume: {best_stock.get('trade_quantity', 'N/A'):,}")


            # Calculate and show key metrics
            if best_stock.get('open_price') and best_stock.get('prev_price'):
                gap_up = (float(best_stock['open_price']) - float(best_stock['prev_price'])) / float(best_stock['prev_price']) * 100
                print(f"Gap Up: {gap_up:.2f}%")
            
            if best_stock.get('high_price') and best_stock.get('ltp'):
                proximity_to_high = (float(best_stock['high_price']) - float(best_stock['ltp'])) / float(best_stock['high_price']) * 100
                print(f"Near High: {proximity_to_high:.2f}% away")
            
            print(f"Momentum Score: {best_score:.1f}/100")
            print("=" * 60)
            
            # Pattern analysis
            net_price_val = float(best_stock.get('net_price', best_stock.get('perChange', 0)))
            print(f"\n📈 PATTERN ANALYSIS:")
            
            if 12 <= net_price_val <= 18:
                print(f"✅ Perfect pattern match ({net_price_val:.2f}% up)")
                print(f"   Expected: Continue rising to 18-20% by market close")
            elif net_price_val > 18:
                print(f"⚠️  Already strong ({net_price_val:.2f}% up)")
                print(f"   May continue if volume sustains")
            else:
                print(f"📊 Moderate momentum ({net_price_val:.2f}% up)")
                print(f"   Needs volume confirmation")
            

            
            return best_stock['symbol']
        else:
            print("Could not identify a strong candidate")
            return None
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Run the function
if __name__ == "__main__":
    stock_name = get_strongest_gainer()
    
    if stock_name:
        print(f"\nStock identified: {stock_name}")
        print(f"Check at: https://www.nseindia.com/get-quotes/equity?symbol={stock_name}")
