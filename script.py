import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
from nsetools import Nse
import warnings
warnings.filterwarnings('ignore')

class NSEGainerPredictor:
    def __init__(self):
        self.nse = Nse()
        self.current_time = datetime.now()
        self.market_hours = self._is_market_hours()
        
    def _is_market_hours(self):
        """Check if current time is within NSE market hours"""
        current_hour = self.current_time.hour
        current_minute = self.current_time.minute
        
        # NSE market hours: 9:15 AM to 3:30 PM IST
        morning_start = 9 * 60 + 15
        morning_end = 15 * 60 + 30
        current_total = current_hour * 60 + current_minute
        
        return morning_start <= current_total <= morning_end
    
    def get_top_gainers_from_nse(self, limit=20):
        """Fetch top gainers from NSE using nsetools"""
        print("\n" + "="*70)
        print("📈 FETCHING TOP GAINERS FROM NSE")
        print("="*70)
        
        try:
            # Get top gainers from NSE
            top_gainers = self.nse.get_top_gainers(index='ALL')
            
            if not top_gainers:
                print("❌ No data received from NSE")
                print("⚠️ Please check if market is open (9:15 AM - 3:30 PM IST)")
                return pd.DataFrame()
            
            print(f"✅ Received {len(top_gainers)} stocks from NSE")
            
            # Parse the data
            parsed_stocks = []
            for stock in top_gainers:
                try:
                    # Extract key information from the exact structure you provided
                    symbol = stock.get('symbol', '').strip().upper()
                    
                    # Get percentage change (main indicator for top gainers)
                    per_change = stock.get('perChange', 0)
                    if isinstance(per_change, str):
                        per_change = float(per_change.replace('%', ''))
                    
                    # Get current price
                    ltp = stock.get('ltp', 0)
                    if isinstance(ltp, str):
                        ltp = float(ltp.replace(',', ''))
                    
                    # Get previous close
                    prev_price = stock.get('prev_price', 0)
                    if isinstance(prev_price, str):
                        prev_price = float(prev_price.replace(',', ''))
                    
                    # Get today's high and low
                    high_price = stock.get('high_price', ltp)
                    if isinstance(high_price, str):
                        high_price = float(high_price.replace(',', ''))
                    
                    low_price = stock.get('low_price', ltp)
                    if isinstance(low_price, str):
                        low_price = float(low_price.replace(',', ''))
                    
                    # Get volume
                    trade_quantity = stock.get('trade_quantity', 0)
                    if isinstance(trade_quantity, str):
                        trade_quantity = float(trade_quantity.replace(',', ''))
                    
                    # Only include stocks with positive gain
                    if per_change > 0 and symbol:
                        parsed_stocks.append({
                            'symbol': symbol,
                            'gain_percent': per_change,
                            'current_price': ltp,
                            'prev_close': prev_price,
                            'today_high': high_price,
                            'today_low': low_price,
                            'volume': trade_quantity,
                            'open_price': stock.get('open_price', ltp),
                            'turnover': stock.get('turnover', 0)
                        })
                        
                except Exception as e:
                    print(f"  ⚠️ Error parsing {stock.get('symbol', 'Unknown')}: {e}")
                    continue
            
            if not parsed_stocks:
                print("❌ No valid gainers found")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(parsed_stocks)
            
            # Sort by gain percentage
            df = df.sort_values('gain_percent', ascending=False).head(limit)
            
            # Display top gainers
            print(f"\n🏆 TOP {min(10, len(df))} GAINERS:")
            print("-" * 80)
            print(f"{'Rank':<5} {'Symbol':<10} {'Gain %':<10} {'Price':<12} {'High':<12} {'Low':<12} {'Volume':<15}")
            print("-" * 80)
            
            for i, (idx, row) in enumerate(df.head(10).iterrows(), 1):
                print(f"{i:<5} {row['symbol']:<10} {row['gain_percent']:<10.2f} "
                      f"₹{row['current_price']:<10.2f} ₹{row['today_high']:<10.2f} "
                      f"₹{row['today_low']:<10.2f} {row['volume']:>12,.0f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching from NSE: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def analyze_stock_strength(self, symbol, current_data):
        """Analyze if a stock will remain up throughout the day"""
        print(f"\n🔍 Analyzing {symbol}:")
        print(f"   Today's Gain: {current_data['gain_percent']:.2f}%")
        print(f"   Price: ₹{current_data['current_price']:.2f} "
              f"(High: ₹{current_data['today_high']:.2f}, Low: ₹{current_data['today_low']:.2f})")
        
        analysis = {
            'symbol': symbol,
            'gain_percent': current_data['gain_percent'],
            'current_price': current_data['current_price'],
            'today_high': current_data['today_high'],
            'today_low': current_data['today_low'],
            'volume': current_data['volume']
        }
        
        # 1. CHECK CURRENT POSITION AGAINST DAY'S RANGE
        price_range = current_data['today_high'] - current_data['today_low']
        if price_range > 0:
            distance_from_low = current_data['current_price'] - current_data['today_low']
            distance_to_high = current_data['today_high'] - current_data['current_price']
            
            position_in_range = (distance_from_low / price_range) * 100
            
            analysis['position_in_range'] = position_in_range
            analysis['near_high'] = distance_to_high < (price_range * 0.1)  # Within 10% of day's high
            analysis['far_from_low'] = position_in_range > 70  # In top 30% of day's range
            
            print(f"   📊 Position in day's range: {position_in_range:.1f}% "
                  f"(Near High: {'✅' if analysis['near_high'] else '❌'}, "
                  f"Far from Low: {'✅' if analysis['far_from_low'] else '❌'})")
        
        # 2. CHECK IF STOCK IS HOLDING GAINS
        # Calculate if price is above previous close and open
        if 'prev_close' in current_data and current_data['prev_close'] > 0:
            above_prev_close = (current_data['current_price'] > current_data['prev_close'])
            analysis['above_prev_close'] = above_prev_close
            
            if 'open_price' in current_data and current_data['open_price'] > 0:
                above_open = (current_data['current_price'] > current_data['open_price'])
                analysis['above_open'] = above_open
                print(f"   📈 Above Open: {'✅' if above_open else '❌'} | "
                      f"Above Prev Close: {'✅' if above_prev_close else '❌'}")
        
        # 3. GET HISTORICAL DATA FOR TREND ANALYSIS
        try:
            hist_data = self._get_historical_data(symbol)
            if hist_data is not None and not hist_data.empty:
                trend_analysis = self._analyze_trend(hist_data, current_data['current_price'])
                analysis.update(trend_analysis)
                
                # Calculate support and resistance
                support_resistance = self._calculate_support_resistance(hist_data)
                analysis.update(support_resistance)
                
                # Check if current price is above support
                if 'support_level' in analysis:
                    above_support = current_data['current_price'] > analysis['support_level']
                    analysis['above_support'] = above_support
                    support_distance = ((current_data['current_price'] - analysis['support_level']) / 
                                       analysis['support_level'] * 100)
                    analysis['support_distance_pct'] = support_distance
                    
                    print(f"   🛡️  Support: ₹{analysis['support_level']:.2f} "
                          f"(Above: {'✅' if above_support else '❌'}, Distance: {support_distance:.1f}%)")
        except Exception as e:
            print(f"   ⚠️ Historical analysis skipped: {e}")
        
        # 4. CHECK VOLUME STRENGTH
        volume_strength = self._analyze_volume(current_data['volume'], symbol)
        analysis.update(volume_strength)
        
        # 5. CALCULATE WILL IT STAY UP SCORE
        will_stay_up, confidence, score_details = self._predict_will_stay_up(analysis)
        
        analysis['will_stay_up'] = will_stay_up
        analysis['confidence'] = confidence
        analysis['score_details'] = score_details
        
        print(f"   🎯 Prediction: {'✅ WILL STAY UP' if will_stay_up else '❌ MAY DIP'}")
        print(f"   🔒 Confidence: {confidence:.1f}%")
        print(f"   📋 Score: {score_details}")
        
        return analysis
    
    def _get_historical_data(self, symbol):
        """Get historical data for trend analysis"""
        try:
            # Clean symbol
            symbol = symbol.strip().upper()
            
            # Try with .NS suffix
            yf_symbol = f"{symbol}.NS"
            
            # Get last 30 days data
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="1mo")
            
            if hist.empty:
                # Try without suffix
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1mo")
            
            return hist if not hist.empty else None
            
        except Exception as e:
            return None
    
    def _analyze_trend(self, hist_data, current_price):
        """Analyze historical trend"""
        analysis = {}
        
        try:
            if len(hist_data) < 5:
                return analysis
            
            # Calculate moving averages
            hist_data['MA5'] = hist_data['Close'].rolling(window=5).mean()
            hist_data['MA10'] = hist_data['Close'].rolling(window=10).mean()
            hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
            
            latest = hist_data.iloc[-1]
            
            # Check if above moving averages
            analysis['above_ma5'] = current_price > latest['MA5'] if pd.notna(latest['MA5']) else False
            analysis['above_ma10'] = current_price > latest['MA10'] if pd.notna(latest['MA10']) else False
            analysis['above_ma20'] = current_price > latest['MA20'] if pd.notna(latest['MA20']) else False
            
            # Check trend direction (5-day trend)
            if len(hist_data) >= 5:
                prices_5d = hist_data['Close'].tail(5).values
                analysis['uptrend_5d'] = all(prices_5d[i] >= prices_5d[i-1] for i in range(1, 5))
            
            # Calculate RSI
            if len(hist_data) >= 14:
                delta = hist_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
                rs = gain / loss if loss != 0 else 0
                rsi = 100 - (100 / (1 + rs))
                analysis['rsi'] = rsi
                analysis['rsi_safe'] = 30 < rsi < 70  # Not overbought or oversold
            
            return analysis
            
        except Exception as e:
            return analysis
    
    def _calculate_support_resistance(self, hist_data):
        """Calculate support and resistance levels"""
        analysis = {}
        
        try:
            if len(hist_data) < 10:
                return analysis
            
            # Recent support (lowest of last 10 days)
            analysis['support_level'] = hist_data['Low'].tail(10).min()
            
            # Recent resistance (highest of last 10 days)
            analysis['resistance_level'] = hist_data['High'].tail(10).max()
            
            return analysis
            
        except Exception as e:
            return analysis
    
    def _analyze_volume(self, current_volume, symbol):
        """Analyze volume strength"""
        analysis = {}
        
        try:
            # Get historical volume for comparison
            hist_data = self._get_historical_data(symbol)
            if hist_data is not None and not hist_data.empty and len(hist_data) >= 5:
                avg_volume_5d = hist_data['Volume'].tail(5).mean()
                if avg_volume_5d > 0:
                    volume_ratio = current_volume / avg_volume_5d
                    analysis['volume_ratio'] = volume_ratio
                    analysis['high_volume'] = volume_ratio > 1.5
            return analysis
            
        except Exception as e:
            return analysis
    
    def _predict_will_stay_up(self, analysis):
        """Predict if stock will stay up throughout the day"""
        score = 0
        max_score = 100
        details = []
        
        # 1. CURRENT POSITION SCORE (0-30 points)
        current_score = 0
        
        # Position in day's range (prefer near highs)
        if 'position_in_range' in analysis:
            if analysis['position_in_range'] > 80:
                current_score += 15
                details.append("Very high in range (+15)")
            elif analysis['position_in_range'] > 60:
                current_score += 10
                details.append("High in range (+10)")
            elif analysis['position_in_range'] > 40:
                current_score += 5
                details.append("Mid-range (+5)")
        
        # Near day's high
        if analysis.get('near_high', False):
            current_score += 10
            details.append("Near day's high (+10)")
        
        # Far from day's low
        if analysis.get('far_from_low', False):
            current_score += 5
            details.append("Far from low (+5)")
        
        current_score = min(current_score, 30)
        score += current_score
        
        # 2. TREND AND MOMENTUM SCORE (0-30 points)
        trend_score = 0
        
        # Above moving averages
        if analysis.get('above_ma5', False):
            trend_score += 5
            details.append("Above MA5 (+5)")
        if analysis.get('above_ma10', False):
            trend_score += 5
            details.append("Above MA10 (+5)")
        if analysis.get('above_ma20', False):
            trend_score += 5
            details.append("Above MA20 (+5)")
        
        # Uptrend
        if analysis.get('uptrend_5d', False):
            trend_score += 10
            details.append("5-day uptrend (+10)")
        
        # Safe RSI
        if analysis.get('rsi_safe', False):
            trend_score += 5
            details.append("Safe RSI (+5)")
        
        trend_score = min(trend_score, 30)
        score += trend_score
        
        # 3. SUPPORT AND VOLUME SCORE (0-20 points)
        support_score = 0
        
        # Above support
        if analysis.get('above_support', False):
            support_score += 10
            details.append("Above support (+10)")
        
        # High volume
        if analysis.get('high_volume', False):
            support_score += 5
            details.append("High volume (+5)")
        
        # Above open and prev close
        if analysis.get('above_open', False):
            support_score += 3
            details.append("Above open (+3)")
        if analysis.get('above_prev_close', False):
            support_score += 2
            details.append("Above prev close (+2)")
        
        support_score = min(support_score, 20)
        score += support_score
        
        # 4. GAIN STRENGTH SCORE (0-20 points)
        gain_score = 0
        
        # Moderate gains are better than extreme gains
        gain_pct = analysis.get('gain_percent', 0)
        if 2 <= gain_pct <= 8:
            gain_score += 15
            details.append(f"Moderate gain {gain_pct:.1f}% (+15)")
        elif gain_pct > 8:
            gain_score += 5  # Too high might mean profit booking
            details.append(f"High gain {gain_pct:.1f}% (+5)")
        elif gain_pct > 0:
            gain_score += 10
            details.append(f"Small gain {gain_pct:.1f}% (+10)")
        
        gain_score = min(gain_score, 20)
        score += gain_score
        
        # Calculate confidence percentage
        confidence = min(95, 50 + (score * 0.45))
        
        # Determine if will stay up
        will_stay_up = (score >= 60 and 
                       analysis.get('above_support', False) and 
                       analysis.get('position_in_range', 0) > 50)
        
        score_details = f"{score}/100 [Curr:{current_score}, Trend:{trend_score}, Supp:{support_score}, Gain:{gain_score}]"
        
        return will_stay_up, confidence, score_details
    
    def analyze_all_gainers(self, top_gainers_df):
        """Analyze all top gainers"""
        if top_gainers_df.empty:
            print("\n❌ No gainers to analyze")
            return []
        
        print("\n" + "="*70)
        print(f"🔬 ANALYZING {len(top_gainers_df)} TOP GAINERS")
        print("="*70)
        
        analysis_results = []
        
        for idx, row in top_gainers_df.iterrows():
            analysis = self.analyze_stock_strength(row['symbol'], row)
            if analysis:
                analysis_results.append(analysis)
        
        print(f"\n✅ Successfully analyzed {len(analysis_results)} stocks")
        
        return analysis_results
    
    def select_safe_stocks(self, analysis_results):
        """Select stocks that are safe and will stay up"""
        if not analysis_results:
            return []
        
        # Filter stocks that are predicted to stay up
        staying_up_stocks = [a for a in analysis_results if a.get('will_stay_up', False)]
        
        if not staying_up_stocks:
            print("\n⚠️ No stocks are predicted to stay up with high confidence")
            # Return top 3 by confidence anyway
            staying_up_stocks = sorted(analysis_results, 
                                     key=lambda x: x.get('confidence', 0), 
                                     reverse=True)[:3]
        
        # Sort by confidence and score
        safe_stocks = sorted(staying_up_stocks, 
                           key=lambda x: (x.get('confidence', 0), x.get('gain_percent', 0)), 
                           reverse=True)
        
        return safe_stocks[:5]  # Top 5 at most
    
    def generate_final_predictions(self, safe_stocks, all_analysis):
        """Generate final predictions"""
        if not safe_stocks:
            report = "="*70 + "\n"
            report += "❌ NO SAFE STOCKS FOUND\n"
            report += "="*70 + "\n"
            report += "\nNo stocks meet the safety criteria for staying up throughout the day.\n"
            report += "Consider waiting for better opportunities or reducing position sizes.\n"
            report += "="*70
            return report
        
        report = []
        report.append("="*80)
        report.append("🏆 NSE TOP GAINER PREDICTIONS - SAFE STOCKS THAT WILL STAY UP")
        report.append("="*80)
        report.append(f"Generated: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Market Hours: {'✅ OPEN' if self.market_hours else '❌ CLOSED'}")
        report.append(f"Total analyzed: {len(all_analysis)} | Safe picks: {len(safe_stocks)}")
        report.append("="*80)
        
        report.append("\n🎯 SAFE PICKS (Will Stay Up):")
        report.append("-"*80)
        report.append(f"{'Rank':<5} {'Symbol':<10} {'Gain %':<10} {'Price':<12} {'Confidence':<12} {'Position':<15} {'Score':<10}")
        report.append("-"*80)
        
        for i, stock in enumerate(safe_stocks, 1):
            position = f"{stock.get('position_in_range', 0):.1f}%" if 'position_in_range' in stock else "N/A"
            report.append(f"{i:<5} {stock['symbol']:<10} {stock['gain_percent']:<10.2f} "
                         f"₹{stock['current_price']:<10.2f} {stock['confidence']:<11.1f}% "
                         f"{position:<15} {stock['score_details'].split()[0]}")
        
        report.append("\n" + "="*80)
        report.append("📊 DETAILED ANALYSIS OF SAFE PICKS:")
        report.append("="*80)
        
        for i, stock in enumerate(safe_stocks, 1):
            report.append(f"\n{i}. {stock['symbol']}")
            report.append(f"   Today's Gain: {stock['gain_percent']:.2f}%")
            report.append(f"   Current Price: ₹{stock['current_price']:.2f}")
            report.append(f"   Day's Range: ₹{stock['today_low']:.2f} - ₹{stock['today_high']:.2f}")
            
            if 'position_in_range' in stock:
                report.append(f"   Position in Range: {stock['position_in_range']:.1f}% "
                            f"{'(Near High ✅)' if stock.get('near_high') else ''}")
            
            report.append(f"   Confidence to Stay Up: {stock['confidence']:.1f}%")
            report.append(f"   Score Breakdown: {stock['score_details']}")
            
            # Key factors
            factors = []
            if stock.get('above_support', False):
                factors.append("Above Support")
            if stock.get('above_ma5', False):
                factors.append("Above MA5")
            if stock.get('above_open', False):
                factors.append("Above Open")
            if stock.get('high_volume', False):
                factors.append("High Volume")
            
            if factors:
                report.append(f"   ✅ Key Strengths: {', '.join(factors)}")
            
            # Risk assessment
            risk = "LOW" if stock['confidence'] > 80 else "MEDIUM" if stock['confidence'] > 65 else "HIGH"
            report.append(f"   ⚠️ Risk Level: {risk}")
        
        # Trading strategy
        report.append("\n" + "="*80)
        report.append("💡 TRADING STRATEGY FOR SAFE STOCKS:")
        report.append("="*80)
        report.append("For the above safe stocks:")
        report.append("1. ENTRY: Wait for small dips (0.5-1% pullback)")
        report.append("2. STOP LOSS: Set at 2-3% below entry price")
        report.append("3. TARGET: Consider booking partial profits at 3-5% gains")
        report.append("4. MONITOR: Watch for breaking below day's low")
        report.append("5. RISK: Never risk more than 1% of capital per trade")
        
        # Summary of all analyzed stocks
        report.append("\n" + "="*80)
        report.append("📋 SUMMARY OF ALL ANALYZED STOCKS:")
        report.append("="*80)
        report.append(f"{'Symbol':<10} {'Gain %':<8} {'Price':<10} {'Stay Up':<10} {'Confidence':<12} {'Position':<10}")
        report.append("-"*80)
        
        for stock in sorted(all_analysis, key=lambda x: x.get('gain_percent', 0), reverse=True):
            stay_up = "✅ YES" if stock.get('will_stay_up', False) else "❌ NO"
            position = f"{stock.get('position_in_range', 0):.1f}%" if 'position_in_range' in stock else "N/A"
            report.append(f"{stock['symbol']:<10} {stock['gain_percent']:<8.2f} "
                         f"₹{stock['current_price']:<9.2f} {stay_up:<10} "
                         f"{stock['confidence']:<11.1f}% {position:<10}")
        
        # Important warning
        report.append("\n" + "="*80)
        report.append("⚠️ IMPORTANT WARNING - READ CAREFULLY:")
        report.append("="*80)
        report.append("1. These are PREDICTIONS, not guarantees")
        report.append("2. Stock markets can be unpredictable")
        report.append("3. Always use STOP LOSS orders")
        report.append("4. Don't invest more than you can afford to lose")
        report.append("5. Monitor your positions throughout the day")
        report.append("6. This analysis is for EDUCATIONAL PURPOSES only")
        report.append("="*80)
        
        return "\n".join(report)
    
    def save_results(self, safe_stocks, all_analysis):
        """Save analysis results to files"""
        if not safe_stocks:
            return
        
        timestamp = self.current_time.strftime("%Y%m%d_%H%M%S")
        
        # Save all analysis
        if all_analysis:
            detailed_df = pd.DataFrame(all_analysis)
            detailed_df.to_csv(f"nse_all_analysis_{timestamp}.csv", index=False)
        
        # Save safe stocks
        if safe_stocks:
            safe_df = pd.DataFrame(safe_stocks)
            safe_df.to_csv(f"nse_safe_stocks_{timestamp}.csv", index=False)
            
            # Save readable report
            report = self.generate_final_predictions(safe_stocks, all_analysis)
            with open(f"nse_predictions_{timestamp}.txt", 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n💾 Results saved:")
            print(f"   📁 nse_all_analysis_{timestamp}.csv - All analyzed stocks")
            print(f"   📁 nse_safe_stocks_{timestamp}.csv - Safe stocks only")
            print(f"   📁 nse_predictions_{timestamp}.txt - Full report")
    
    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        print("="*80)
        print("🚀 NSE TOP GAINER PREDICTION SYSTEM")
        print("="*80)
        print("🎯 Predicting which top gainers will STAY UP throughout the day")
        print("="*80)
        
        # Step 1: Get top gainers from NSE
        top_gainers = self.get_top_gainers_from_nse(limit=15)
        
        if top_gainers.empty:
            print("\n❌ Cannot proceed without NSE data.")
            if not self.market_hours:
                print("   ⏰ Market is closed (NSE hours: 9:15 AM - 3:30 PM IST)")
            return
        
        # Step 2: Analyze all gainers
        all_analysis = self.analyze_all_gainers(top_gainers)
        
        if not all_analysis:
            print("\n❌ Could not analyze any stocks.")
            return
        
        # Step 3: Select safe stocks that will stay up
        safe_stocks = self.select_safe_stocks(all_analysis)
        
        # Step 4: Generate and display report
        report = self.generate_final_predictions(safe_stocks, all_analysis)
        print("\n" + report)
        
        # Step 5: Save results
        # if safe_stocks:
        #     self.save_results(safe_stocks, all_analysis)
        
        # Final summary
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        
        if safe_stocks:
            print(f"\n🎯 {len(safe_stocks)} SAFE STOCK(S) IDENTIFIED:")
            for stock in safe_stocks:
                print(f"   • {stock['symbol']} - Gain: {stock['gain_percent']:.1f}% | "
                      f"Confidence: {stock['confidence']:.1f}% | "
                      f"Price: ₹{stock['current_price']:.2f}")
            
            print("\n💡 Key factors considered for 'will stay up':")
            print("   1. Position in day's range (near highs is better)")
            print("   2. Above key support levels")
            print("   3. Moderate gains (not too extreme)")
            print("   4. Healthy volume")
            print("   5. Positive trend indicators")
        else:
            print("\n⚠️ NO SAFE STOCKS FOUND")
            print("   Consider these alternatives:")
            print("   1. Wait for better market conditions")
            print("   2. Look for stocks with smaller gains (1-3%)")
            print("   3. Consider defensive sectors")
            print("   4. Reduce position sizes if you must trade")
        
        print("\n" + "="*80)
        print("📌 Remember: Safety first! Trade only what you can afford to lose.")
        print("="*80)

# Main execution
if __name__ == "__main__":
    try:
        print("🔧 Initializing NSE Analyzer...")
        analyzer = NSEGainerPredictor()
        analyzer.run_complete_analysis()
    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
