"""
30-Day Trading Plan Generator for $100 Portfolio
Optimized for 5 trades/day with cross margin
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json


class TradingPlanGenerator:
    """Generate 30-day trading plan with optimal position sizing"""

    def __init__(self, starting_capital: float = 100.0):
        self.starting_capital = starting_capital
        self.current_capital = starting_capital

        # Historical performance data
        self.stats = {
            'HIGH': {
                'win_rate': 0.625,
                'avg_win': 6.88,
                'avg_loss': 1.57,
                'trades': 24,
                'pnl': 93.90,
                'per_trade': 3.91
            },
            'MEDIUM': {
                'win_rate': 0.50,
                'avg_win': 6.88,
                'avg_loss': 1.57,
                'trades': 10,
                'pnl': 11.16,
                'per_trade': 1.12
            }
        }

        # Strategy distribution
        self.strategy_dist = {
            'Q-Pulse': 0.75,
            'Q-Trend': 0.23,
            'Q-Mean-Rev': 0.02
        }

        # Confidence distribution (HIGH/MEDIUM only)
        self.confidence_dist = {
            'HIGH': 0.68,    # 68% of trades
            'MEDIUM': 0.32   # 32% of trades
        }

        # Kelly fractions (base for $100)
        self.kelly_fractions = {
            'HIGH': 0.146,
            'MEDIUM': 0.110
        }

        # Aggressive multiplier for "max output"
        # Using 1.5x Kelly is aggressive but still safe given the edge
        self.aggression_multiplier = 1.5

        # Cross margin leverage limits by confidence
        self.max_leverage = {
            'HIGH': 10,      # Can use up to 10x
            'MEDIUM': 5,     # More conservative for medium
        }

    def calculate_position_size(
        self,
        confidence: str,
        strategy: str,
        current_capital: float
    ) -> Dict:
        """
        Calculate position size for given confidence and strategy

        Returns position details including leverage recommendation
        """
        # Base Kelly position
        base_kelly = self.kelly_fractions[confidence]

        # Apply aggression multiplier for max output
        adjusted_kelly = base_kelly * self.aggression_multiplier

        # Calculate position size
        position_size = current_capital * adjusted_kelly

        # Cap at reasonable maximum (50% of capital for single position)
        max_single_position = current_capital * 0.50
        position_size = min(position_size, max_single_position)

        # Recommended leverage
        recommended_leverage = self.max_leverage[confidence]

        # Margin requirement
        margin_required = position_size / recommended_leverage

        # Risk calculation (2% stop loss)
        stop_loss_pct = 0.02
        risk_amount = position_size * stop_loss_pct
        risk_pct = (risk_amount / current_capital) * 100

        return {
            'confidence': confidence,
            'strategy': strategy,
            'position_size': position_size,
            'recommended_leverage': recommended_leverage,
            'margin_required': margin_required,
            'stop_loss_pct': stop_loss_pct * 100,
            'risk_amount': risk_amount,
            'risk_pct_of_capital': risk_pct,
            'kelly_fraction': adjusted_kelly * 100
        }

    def generate_trade_distribution(self, total_days: int = 30, trades_per_day: int = 5) -> pd.DataFrame:
        """
        Generate trade distribution for the entire period
        """
        total_trades = total_days * trades_per_day

        # Distribute by confidence
        high_trades = int(total_trades * self.confidence_dist['HIGH'])
        medium_trades = total_trades - high_trades

        # Distribute HIGH confidence by strategy
        high_qpulse = int(high_trades * self.strategy_dist['Q-Pulse'])
        high_qtrend = int(high_trades * self.strategy_dist['Q-Trend'])
        high_meanrev = high_trades - high_qpulse - high_qtrend

        # Distribute MEDIUM confidence by strategy
        med_qpulse = int(medium_trades * self.strategy_dist['Q-Pulse'])
        med_qtrend = int(medium_trades * self.strategy_dist['Q-Trend'])
        med_meanrev = medium_trades - med_qpulse - med_qtrend

        distribution = {
            'HIGH': {
                'Q-Pulse': high_qpulse,
                'Q-Trend': high_qtrend,
                'Q-Mean-Rev': high_meanrev,
                'Total': high_trades
            },
            'MEDIUM': {
                'Q-Pulse': med_qpulse,
                'Q-Trend': med_qtrend,
                'Q-Mean-Rev': med_meanrev,
                'Total': medium_trades
            }
        }

        return distribution

    def generate_daily_plan(self, day: int, trades_remaining: Dict) -> List[Dict]:
        """
        Generate specific trade plan for a single day
        """
        daily_trades = []

        # Target 5 trades per day: ~3-4 HIGH, ~1-2 MEDIUM
        high_today = min(np.random.choice([3, 4], p=[0.4, 0.6]),
                        trades_remaining['HIGH']['Total'])
        medium_today = min(5 - high_today, trades_remaining['MEDIUM']['Total'])

        # Generate HIGH confidence trades
        for _ in range(high_today):
            strategy = self._pick_strategy('HIGH', trades_remaining)
            if strategy:
                position = self.calculate_position_size('HIGH', strategy, self.current_capital)
                daily_trades.append(position)
                trades_remaining['HIGH'][strategy] -= 1
                trades_remaining['HIGH']['Total'] -= 1

        # Generate MEDIUM confidence trades
        for _ in range(medium_today):
            strategy = self._pick_strategy('MEDIUM', trades_remaining)
            if strategy:
                position = self.calculate_position_size('MEDIUM', strategy, self.current_capital)
                daily_trades.append(position)
                trades_remaining['MEDIUM'][strategy] -= 1
                trades_remaining['MEDIUM']['Total'] -= 1

        return daily_trades

    def _pick_strategy(self, confidence: str, trades_remaining: Dict) -> str:
        """Pick strategy based on remaining distribution"""
        strategies = ['Q-Pulse', 'Q-Trend', 'Q-Mean-Rev']
        remaining = [trades_remaining[confidence][s] for s in strategies]

        if sum(remaining) == 0:
            return None

        # Weighted random choice based on remaining
        probs = np.array(remaining) / sum(remaining)
        return np.random.choice(strategies, p=probs)

    def project_outcomes(self, days: int = 30, trades_per_day: int = 5) -> Dict:
        """
        Project expected outcomes over the period
        """
        total_trades = days * trades_per_day
        distribution = self.generate_trade_distribution(days, trades_per_day)

        # Calculate expected PnL
        high_trades = distribution['HIGH']['Total']
        medium_trades = distribution['MEDIUM']['Total']

        high_pnl_per_trade = self.stats['HIGH']['per_trade']
        medium_pnl_per_trade = self.stats['MEDIUM']['per_trade']

        # Scale by position size relative to historical
        # Historical was ~$146 position for HIGH, we're using ~$22 for $100 portfolio
        position_scale = (self.starting_capital * self.kelly_fractions['HIGH'] * self.aggression_multiplier) / 146.0

        expected_high_pnl = high_trades * high_pnl_per_trade * position_scale
        expected_medium_pnl = medium_trades * medium_pnl_per_trade * position_scale
        expected_total_pnl = expected_high_pnl + expected_medium_pnl

        # Expected final capital (conservative estimate)
        # Use lower multiplier for compounding projection
        conservative_pnl = expected_total_pnl * 0.7  # 30% haircut for safety
        expected_final = self.starting_capital + conservative_pnl

        # Calculate expected win/loss counts
        expected_wins = int(high_trades * self.stats['HIGH']['win_rate'] +
                           medium_trades * self.stats['MEDIUM']['win_rate'])
        expected_losses = total_trades - expected_wins

        return {
            'total_trades': total_trades,
            'distribution': distribution,
            'expected_wins': expected_wins,
            'expected_losses': expected_losses,
            'expected_win_rate': expected_wins / total_trades * 100,
            'expected_pnl': expected_total_pnl,
            'conservative_pnl': conservative_pnl,
            'expected_final_capital': expected_final,
            'expected_roi': (expected_final - self.starting_capital) / self.starting_capital * 100,
            'avg_pnl_per_trade': expected_total_pnl / total_trades,
            'starting_capital': self.starting_capital,
        }

    def generate_full_30day_plan(self) -> Dict:
        """
        Generate complete 30-day trading plan
        """
        distribution = self.generate_trade_distribution(30, 5)
        projections = self.project_outcomes(30, 5)

        # Position sizing table
        position_table = {}
        for confidence in ['HIGH', 'MEDIUM']:
            position_table[confidence] = {}
            for strategy in ['Q-Pulse', 'Q-Trend', 'Q-Mean-Rev']:
                position_table[confidence][strategy] = self.calculate_position_size(
                    confidence, strategy, self.starting_capital
                )

        return {
            'starting_capital': self.starting_capital,
            'trade_distribution': distribution,
            'projections': projections,
            'position_sizing': position_table,
            'daily_target': {
                'total_trades': 5,
                'high_confidence': '3-4 trades',
                'medium_confidence': '1-2 trades'
            },
            'risk_management': {
                'stop_loss': '2% on every trade',
                'max_leverage_high': 10,
                'max_leverage_medium': 5,
                'max_single_position': self.starting_capital * 0.50,
                'max_total_exposure': self.starting_capital * 2.0  # With cross margin
            }
        }

    def print_trading_plan(self):
        """Print formatted trading plan"""
        plan = self.generate_full_30day_plan()

        print("=" * 100)
        print(f"30-DAY TRADING PLAN - ${self.starting_capital:.2f} PORTFOLIO")
        print("Cross Margin | 5 Trades/Day | Max Output Strategy")
        print("=" * 100)
        print()

        # Position Sizing Table
        print("📊 POSITION SIZING BY CONFIDENCE & STRATEGY")
        print("-" * 100)
        print(f"{'Confidence':<12} {'Strategy':<15} {'Position':<12} {'Leverage':<10} "
              f"{'Margin':<10} {'Risk $':<10} {'Risk %':<8}")
        print("-" * 100)

        for confidence in ['HIGH', 'MEDIUM']:
            for strategy in ['Q-Pulse', 'Q-Trend', 'Q-Mean-Rev']:
                pos = plan['position_sizing'][confidence][strategy]
                print(f"{confidence:<12} {strategy:<15} "
                      f"${pos['position_size']:<11.2f} {pos['recommended_leverage']:<10}x "
                      f"${pos['margin_required']:<9.2f} ${pos['risk_amount']:<9.2f} "
                      f"{pos['risk_pct_of_capital']:<7.2f}%")
            print()

        print("=" * 100)
        print()

        # Trade Distribution
        print("📈 30-DAY TRADE DISTRIBUTION (150 Total Trades)")
        print("-" * 100)
        dist = plan['trade_distribution']
        print(f"{'Confidence':<12} {'Q-Pulse':<10} {'Q-Trend':<10} {'Q-Mean-Rev':<12} {'Total':<10}")
        print("-" * 100)
        for confidence in ['HIGH', 'MEDIUM']:
            d = dist[confidence]
            print(f"{confidence:<12} {d['Q-Pulse']:<10} {d['Q-Trend']:<10} "
                  f"{d['Q-Mean-Rev']:<12} {d['Total']:<10}")
        print("-" * 100)
        total = dist['HIGH']['Total'] + dist['MEDIUM']['Total']
        print(f"{'TOTAL':<12} "
              f"{dist['HIGH']['Q-Pulse'] + dist['MEDIUM']['Q-Pulse']:<10} "
              f"{dist['HIGH']['Q-Trend'] + dist['MEDIUM']['Q-Trend']:<10} "
              f"{dist['HIGH']['Q-Mean-Rev'] + dist['MEDIUM']['Q-Mean-Rev']:<12} "
              f"{total:<10}")
        print()
        print("=" * 100)
        print()

        # Expected Outcomes
        print("🎯 EXPECTED OUTCOMES")
        print("-" * 100)
        proj = plan['projections']
        print(f"  Starting Capital:        ${proj['starting_capital']:.2f}")
        print(f"  Expected Final Capital:  ${proj['expected_final_capital']:.2f}")
        print(f"  Expected Profit:         ${proj['conservative_pnl']:.2f}")
        print(f"  Expected ROI:            {proj['expected_roi']:.1f}%")
        print()
        print(f"  Expected Win Rate:       {proj['expected_win_rate']:.1f}%")
        print(f"  Expected Wins:           {proj['expected_wins']}")
        print(f"  Expected Losses:         {proj['expected_losses']}")
        print(f"  Avg Profit per Trade:    ${proj['avg_pnl_per_trade']:.2f}")
        print()
        print("=" * 100)
        print()

        # Daily Execution Guide
        print("📋 DAILY EXECUTION GUIDE")
        print("-" * 100)
        print("  Target: 5 trades per day")
        print("  Typical Distribution:")
        print("    - 3-4 HIGH confidence trades")
        print("    - 1-2 MEDIUM confidence trades")
        print()
        print("  Strategy Split (approximate):")
        print("    - 75% Q-Pulse (momentum trades)")
        print("    - 23% Q-Trend (trend-following)")
        print("    - 2% Q-Mean-Rev (mean reversion)")
        print()
        print("=" * 100)
        print()

        # Risk Management
        print("⚠️  RISK MANAGEMENT RULES")
        print("-" * 100)
        rm = plan['risk_management']
        print(f"  Stop Loss:              {rm['stop_loss']}")
        print(f"  Max Leverage (HIGH):    {rm['max_leverage_high']}x")
        print(f"  Max Leverage (MEDIUM):  {rm['max_leverage_medium']}x")
        print(f"  Max Single Position:    ${rm['max_single_position']:.2f}")
        print(f"  Max Total Exposure:     ${rm['max_total_exposure']:.2f}")
        print()
        print("  HALT TRADING IF:")
        print("    - Daily loss exceeds 10% of capital")
        print("    - Win rate drops below 40% over last 25 trades")
        print("    - 3 consecutive days of losses")
        print("    - Total drawdown exceeds 20%")
        print()
        print("=" * 100)

        return plan

    def export_plan(self, filename: str = "30day_trading_plan.json"):
        """Export plan to JSON"""
        plan = self.generate_full_30day_plan()

        # Convert to serializable format
        export_data = {
            'starting_capital': self.starting_capital,
            'duration_days': 30,
            'trades_per_day': 5,
            'total_trades': 150,
            'position_sizing': {
                conf: {
                    strat: {k: float(v) if isinstance(v, (int, float)) else v
                           for k, v in pos.items()}
                    for strat, pos in strategies.items()
                }
                for conf, strategies in plan['position_sizing'].items()
            },
            'trade_distribution': plan['trade_distribution'],
            'projections': {k: float(v) if isinstance(v, (int, float)) else v
                          for k, v in plan['projections'].items()},
            'daily_target': plan['daily_target'],
            'risk_management': plan['risk_management']
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✅ 30-day plan exported to {filename}")


def main():
    """Generate and display 30-day trading plan"""
    print("\n")
    print("=" * 100)
    print("30-DAY MAXIMUM OUTPUT TRADING PLAN GENERATOR")
    print("=" * 100)
    print()

    generator = TradingPlanGenerator(starting_capital=100.0)
    plan = generator.print_trading_plan()

    # Export to JSON
    generator.export_plan("30day_trading_plan_100.json")

    print("\n")
    print("=" * 100)
    print("NEXT STEPS")
    print("=" * 100)
    print()
    print("1. Review position sizing for each confidence/strategy combination")
    print("2. Set up cross margin on your exchange")
    print("3. Create daily tracking spreadsheet (template below)")
    print("4. Start with Day 1: Target 3-4 HIGH + 1-2 MEDIUM trades")
    print("5. Adjust position sizes daily as capital grows")
    print()
    print("📁 Files generated:")
    print("  - 30day_trading_plan_100.json")
    print()


if __name__ == "__main__":
    main()
