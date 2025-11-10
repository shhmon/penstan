import pandas as pd
import numpy as np
from pstan.processors import Processor

class Base(Processor):
    def __init__(
        self, 
        window = 12,
    ):
        self.window = window

    def detect_bullish_divergence(self, price, indicator, window):
        """Detects bullish divergence: price down, indicator up"""
        price_trend = price.diff(window)
        ind_trend = indicator.diff(window)
        return (price_trend < 0) & (ind_trend > 0)

    def process(self, df: pd.DataFrame):
        df = df.copy()
        
        # --- Price Metrics ---
        df['Close_roll_pct_change'] = df['Close_roll'].pct_change().fillna(0)

        # =============================================================================
        # ADVANCED PRICE ACTION METRICS
        # =============================================================================
        
        # --- Candle Body & Shadow Analysis ---
        df['Body_range_ratio'] = abs(df['Gain']) / df['Range'].replace(0, np.nan)
        df['Upper_shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['Lower_shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        df['Shadow_ratio'] = df['Lower_shadow'] / (df['Upper_shadow'].replace(0, 0.0001))
        
        # --- Range Metrics ---
        df['Range_expansion'] = df['Range_pct'] > df['Range_pct'].rolling(self.window).mean() * 1.5
        
        # --- Explosive Range (key for penny stocks) ---
        df['Explosive_range'] = df['Range_pct'] > 0.20  # 20%+ intraday range
        
        # --- Price Velocity (rate of change) ---
        df['Price_velocity'] = df['Close'].pct_change(periods=1)
        df['Rapid_price_move'] = abs(df['Price_velocity']) > 0.05  # 5% per bar
        
        
        
        # =============================================================================
        # DIVERGENCE DETECTION
        # =============================================================================
        
        df['Bullish_divergence_OBV'] = self.detect_bullish_divergence(df['Close'], df['OBV'], self.window)
        df['Bullish_divergence_RSI'] = self.detect_bullish_divergence(df['Close'], df['RSI'], self.window)
        
        # =============================================================================
        # SIMPLE SIGNAL COMPONENTS
        # =============================================================================
        
        # --- Volume Signals (only during regular hours) ---
        df['Volume_spike'] = (
            df['Is_regular_hours'] & 
            (df['Volume_pct_change_regular'] > 5.0)  # 500% increase
        )
        df['Volume_spike_near'] = (df['Volume_spike'].astype(int).rolling(self.window).sum() > 0)
        df['Momentum_spike'] = (
            df['Volume_confirmable'] & 
            (df['Volume_momentum_norm'] > 2.0)  # 2 std devs
        )
        
        # --- Sentiment Signals ---
        rolling_sentiment = df['Volume_sentiment'].rolling(self.window*2)
        df['Bullish_sentiment'] = (
            df['Volume_sentiment'] > (rolling_sentiment.mean() + 2 * rolling_sentiment.std())
        )
        
        # --- Bollinger Signals ---
        df['Boll_squeeze_near'] = (df['Boll_squeeze'].astype(int).rolling(self.window).sum() > 0)
        
        # --- Volatility Signals ---
        df['Volatility_expansion'] = (df['ATR'] > df['ATR'].rolling(self.window).mean() * 1.5)
        
        # --- Price Signals ---
        df['Sustained_gain'] = (
            (df['Gain'] > 0) & 
            (df['Gain'].rolling(self.window//2).apply(lambda x: (x > 0).sum()) >= self.window//2 * 0.75)
        )
        
        # --- RSI Signals ---
        df['RSI_pos'] = (df['RSI'] >= 60)
        df['RSI_neg'] = (df['RSI'] <= 40)
        df['RSI_aligned_bullish'] = (df['RSI_fast'] > 50) & (df['RSI_slow'] > 50)
        
        # --- Breakout Signal ---
        df['Break'] = (abs(df['Gain']) > 1.9 * df['ATR']) | (df['Range'] > 1.9 * df['ATR'])
        
        # =============================================================================
        # PENNY STOCK SPIKE DETECTION SIGNALS
        # =============================================================================
        
        # --- SPIKE DETECTED: Early detection (0-2 bars into spike) ---
        # Primary signal for detecting when a spike is happening NOW
        df['Spike_detected'] = (
            (
                # Price-based (always reliable, no volume dependency)
                (df['Big_gap_up'] | df['Explosive_range']) &    # Unusual price movement
                (df['Range_pct'] > 0.15) &                        # At least 15% range
                (df['Close'] > df['Open']) &                     # Green candle
                (df['Body_range_ratio'] > 0.5) &                  # Decent body (not all wicks)
                (
                    df['New_HOD'] |                               # Breaking high of day OR
                    (df['Close'] > df['Boll_h'])                 # Breaking Bollinger upper
                )
            ) &
            (
                # Volume confirmation (when available, otherwise skip)
                (
                    df['Is_prepost'] |                            # Skip volume check in pre/post OR
                    (df['Volume_ratio'] > 2.0)                    # High volume during regular
                )
            ) &
            (
                # Momentum confirmation
                (df['Spike_momentum'] | df['Rapid_price_move'])  # Multiple greens OR rapid move
            )
        )
        
        # --- PRICE ACTION BREAKOUT: Pure price-based (no volume) ---
        # Works in pre/post market when volume is missing
        df['Price_breakout'] = (
            (df['Close'] > df['Boll_h']) &                       # Above upper band
            (df['Explosive_range'] | df['Big_gap_up']) &         # Large move
            (df['Close'] > df['Open']) &                         # Green
            (df['Body_range_ratio'] > 0.6) &                      # Strong body
            (df['New_HOD'])                                       # New high of day
        )
        
        # --- VOLATILITY SPIKE: Range expansion ---
        df['Volatility_breakout'] = (
            (df['ATR'] > df['ATR'].rolling(self.window).mean() * 1.5) &  # ATR expanding
            (df['Range_expansion']) &                                  # Range > average
            (df['Rapid_price_move']) &                                 # Fast price move
            (df['Close'] > df['Open'])                                # Green
        )
        
        # --- MOMENTUM BUILDING: Early signs before full spike ---
        # Lower threshold, catches more but with less certainty
        df['Momentum_building'] = (
            (df['Range_pct'] > 0.08) &                            # 8%+ range (lower threshold)
            (df['Green_streak'] >= 2) &                           # 2+ consecutive greens
            (df['Close'] > df['Boll_m']) &                       # Above mid-band
            (
                df['Is_prepost'] |                                # Skip volume in pre/post OR
                (df['Volume_ratio'] > 1.5)                        # Above average volume
            )
        )
        
        # --- GAP AND RUN: Gap up followed by continuation ---
        df['Gap_and_run'] = (
            (df['Big_gap_up']) &                                  # Gapped up significantly
            (df['Close'] > df['Open']) &                         # Continued upward (green)
            (df['New_HOD']) &                                     # Made new high
            (df['Body_range_ratio'] > 0.5)                        # Strong conviction
        )
        
        # =============================================================================
        # LEGACY COMPOSITE SIGNALS (now with pre/post handling)
        # =============================================================================
        
        # --- PRE-BREAKOUT: Compression phase before the move ---
        df['Pre_breakout'] = (
            (df['ATR_compression']) &                             # Volatility contracting
            (df['Boll_squeeze']) &                                # Price range tight
            (df['Volume_elevated_count'].fillna(0) >= 2) &        # Volume building (if available)
            (df['Volume_trend'].fillna(0) == 1) &                 # Volume trending up
            (df['Distance_to_resistance'] < 0.05) &               # Near resistance
            (df['Body_range_ratio'] > 0.5)                        # Strong conviction
        )
        
        # --- ACCUMULATION: Smart money building positions ---
        df['Accumulation'] = (
            (df['Price_efficiency'] < 0.3) &                      # Price choppy
            (df['OBV_change'] > 0.05) &                           # OBV rising
            (df['Buy_sell_ratio'].fillna(1) > 1.3) &              # More buying (if available)
            (df['Volume_ratio'].fillna(0) > 1.5) &                # Above average volume
            (df['Volume_elevated_count'].fillna(0) >= 3) &        # Sustained volume
            (~df['Boll_breakout_h']) &                            # Haven't broken out
            (df['Is_regular_hours'])                              # Only during regular hours
        )
        
        # --- MOMENTUM IGNITION: Early stage breakout ---
        df['Momentum_ignition'] = (
            (df['Volume_acceleration'].fillna(0) > 0) &           # Volume accelerating
            (df['Volume_ratio'].fillna(0) > 3) &                  # Strong volume (if available)
            (df['Close'] > df['Boll_m']) &                       # Above mid-band
            (df['Money_flow_ratio'].fillna(1) > 2) &              # Money flowing in
            (df['Green_streak'] >= 2) &                           # Consecutive greens
            (df['ATR_trend'] > 0) &                               # Volatility expanding
            (df['RSI'] > 45) & (df['RSI'] < 70)                  # RSI has room
        )
        
        # --- BREAKOUT CONFIRMED: For entering after move starts ---
        df['Breakout_confirmed'] = (
            (df['Pre_breakout'].shift(1) | df['Pre_breakout'].shift(2)) &  # Was coiling
            (df['Close'] > df['Boll_h']) &                       # Broke upper band
            (df['Volume_ratio'].fillna(0) > 4) &                  # Strong volume (if available)
            (df['Range_expansion']) &                             # Range expanding
            (df['Body_range_ratio'] > 0.6) &                      # Strong conviction
            (df['Shadow_ratio'] > 1)                              # Bullish structure
        )
        
        # --- LEGACY SIGNALS (from original code) ---
        df['Price_vol_breakout'] = (df['Close_roll_pct_change'] > 0.1) & (df['Volume_ratio'] > 3)
        
        df['Medium_signal'] = (
            (df['Boll_breakout_h']) &
            (df['Volume_spike_near'] | df['Volatility_expansion']) &
            (df['RSI_pos']) &
            (df['Gain'].diff() > 0)
        )
        
        df['Strong_signal'] = (
            (df['Medium_signal']) &
            (df['Price_vol_breakout']) & 
            (df['Break']) & 
            (df['Sustained_gain']) &
            (df['Volume_sentiment'] > 0) &
            (df['Bullish_sentiment'])
        )

        return df
