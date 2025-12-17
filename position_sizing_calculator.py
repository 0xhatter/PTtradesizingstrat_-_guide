"""
Position Sizing Calculator for $1,000 Portfolio
Provides practical Kelly Criterion-based position sizing with risk management overlays
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import json


@dataclass
class PortfolioConfig:
    """Portfolio configuration"""
    total_capital: float = 1000.0

    # Kelly fractions by confidence
    high_conf_kelly: float = 0.146  # 1/3 Kelly
    medium_conf_kelly: float = 0.110  # 1/4 Kelly
    low_conf_kelly: float = 0.055  # 1/8 Kelly

    # Historical confidence distribution
    high_conf_pct: float = 0.67
    medium_conf_pct: float = 0.31
    low_conf_pct: float = 0.02

    # Risk constraints
    max_position_pct: float = 0.20  # Never exceed 20% in single trade
    max_total_exposure_pct: float = 1.50  # Max 150% total across all trades
    correlation_reduction_pct: float = 0.30  # Reduce 30% for correlated assets

    # Margin requirements (typical for crypto perpetuals)
    margin_requirement_pct: float = 0.05  # 5% initial margin (20x max leverage)

    # Stop loss as % of position
    stop_loss_pct: float = 0.02  # 2% stop loss


class PositionSizingCalculator:
    """
    Calculate optimal position sizes for trading strategy
    """

    def __init__(self, config: PortfolioConfig):
        self.config = config

    def calculate_base_position_size(self, confidence: str) -> float:
        """
        Calculate base position size using Kelly Criterion

        Args:
            confidence: 'HIGH', 'MEDIUM', or 'LOW'

        Returns:
            Position size in dollars
        """
        kelly_fractions = {
            'HIGH': self.config.high_conf_kelly,
            'MEDIUM': self.config.medium_conf_kelly,
            'LOW': self.config.low_conf_kelly
        }

        kelly_fraction = kelly_fractions.get(confidence, self.config.low_conf_kelly)
        base_size = self.config.total_capital * kelly_fraction

        # Apply maximum position constraint
        max_position = self.config.total_capital * self.config.max_position_pct
        position_size = min(base_size, max_position)

        return position_size

    def calculate_margin_requirement(self, position_size: float, leverage: float = 1.0) -> float:
        """
        Calculate margin requirement for position

        Args:
            position_size: Notional position size in dollars
            leverage: Leverage multiplier (1 = no leverage)

        Returns:
            Required margin in dollars
        """
        return position_size * self.config.margin_requirement_pct / leverage

    def calculate_position_with_leverage(
        self,
        confidence: str,
        leverage: float = 1.0,
        current_exposure: float = 0.0,
        is_correlated: bool = False
    ) -> Dict:
        """
        Calculate complete position sizing with all adjustments

        Args:
            confidence: Trade confidence level
            leverage: Leverage to use (1-20x typical for crypto)
            current_exposure: Current total exposure across all open positions
            is_correlated: Whether this trade correlates with existing positions

        Returns:
            Dictionary with position details
        """
        # Step 1: Calculate base Kelly position size
        base_size = self.calculate_base_position_size(confidence)

        # Step 2: Apply correlation adjustment if needed
        if is_correlated:
            adjusted_size = base_size * (1 - self.config.correlation_reduction_pct)
        else:
            adjusted_size = base_size

        # Step 3: Check total exposure constraint
        max_allowed_exposure = self.config.total_capital * self.config.max_total_exposure_pct
        remaining_exposure = max_allowed_exposure - current_exposure

        if remaining_exposure <= 0:
            return {
                'allowed': False,
                'reason': 'Maximum total exposure reached',
                'position_size': 0,
                'margin_required': 0,
                'leverage': leverage,
            }

        # Adjust size if it would exceed total exposure limit
        final_position_size = min(adjusted_size, remaining_exposure)

        # Step 4: Calculate margin requirement
        margin_required = self.calculate_margin_requirement(final_position_size, leverage)

        # Step 5: Check if we have enough capital for margin
        if margin_required > self.config.total_capital:
            return {
                'allowed': False,
                'reason': 'Insufficient capital for margin requirement',
                'position_size': final_position_size,
                'margin_required': margin_required,
                'leverage': leverage,
            }

        # Step 6: Calculate risk metrics
        stop_loss_distance = self.config.stop_loss_pct
        risk_amount = final_position_size * stop_loss_distance

        return {
            'allowed': True,
            'confidence': confidence,
            'base_kelly_size': base_size,
            'position_size': final_position_size,
            'margin_required': margin_required,
            'leverage': leverage,
            'stop_loss_pct': stop_loss_distance * 100,
            'risk_amount': risk_amount,
            'risk_pct_of_capital': (risk_amount / self.config.total_capital) * 100,
            'correlation_adjusted': is_correlated,
        }

    def generate_position_sizing_table(self) -> Dict[str, Dict]:
        """
        Generate comprehensive position sizing table for all scenarios
        """
        confidence_levels = ['HIGH', 'MEDIUM', 'LOW']
        leverage_options = [1, 2, 5, 10]

        results = {}

        for confidence in confidence_levels:
            results[confidence] = {}

            for leverage in leverage_options:
                position = self.calculate_position_with_leverage(
                    confidence=confidence,
                    leverage=leverage,
                    current_exposure=0.0,
                    is_correlated=False
                )
                results[confidence][f'{leverage}x'] = position

        return results

    def print_position_sizing_table(self):
        """
        Print formatted position sizing table
        """
        print("=" * 100)
        print(f"POSITION SIZING TABLE - ${self.config.total_capital:,.2f} Portfolio")
        print("=" * 100)
        print()

        table = self.generate_position_sizing_table()

        for confidence in ['HIGH', 'MEDIUM', 'LOW']:
            print(f"\n{confidence} CONFIDENCE")
            print("-" * 100)
            print(f"{'Leverage':<10} {'Position Size':<15} {'Margin Req':<15} "
                  f"{'Risk ($)':<12} {'Risk %':<10} {'Stop Loss %':<12}")
            print("-" * 100)

            for leverage_str in ['1x', '2x', '5x', '10x']:
                pos = table[confidence][leverage_str]

                if pos['allowed']:
                    print(f"{leverage_str:<10} "
                          f"${pos['position_size']:<14.2f} "
                          f"${pos['margin_required']:<14.2f} "
                          f"${pos['risk_amount']:<11.2f} "
                          f"{pos['risk_pct_of_capital']:<9.2f}% "
                          f"{pos['stop_loss_pct']:<11.2f}%")
                else:
                    print(f"{leverage_str:<10} NOT ALLOWED - {pos['reason']}")

        print("\n" + "=" * 100)

    def calculate_portfolio_distribution(self, num_trades: int = 100) -> Dict:
        """
        Calculate expected position distribution over N trades

        Args:
            num_trades: Number of trades to project

        Returns:
            Distribution statistics
        """
        # Based on historical confidence distribution
        expected_high = int(num_trades * self.config.high_conf_pct)
        expected_medium = int(num_trades * self.config.medium_conf_pct)
        expected_low = num_trades - expected_high - expected_medium

        # Calculate total capital deployment
        high_size = self.calculate_base_position_size('HIGH')
        medium_size = self.calculate_base_position_size('MEDIUM')
        low_size = self.calculate_base_position_size('LOW')

        total_high_capital = expected_high * high_size
        total_medium_capital = expected_medium * medium_size
        total_low_capital = expected_low * low_size

        avg_position_size = (total_high_capital + total_medium_capital + total_low_capital) / num_trades

        return {
            'total_trades': num_trades,
            'distribution': {
                'HIGH': {
                    'count': expected_high,
                    'percentage': self.config.high_conf_pct * 100,
                    'position_size': high_size,
                    'total_capital': total_high_capital,
                },
                'MEDIUM': {
                    'count': expected_medium,
                    'percentage': self.config.medium_conf_pct * 100,
                    'position_size': medium_size,
                    'total_capital': total_medium_capital,
                },
                'LOW': {
                    'count': expected_low,
                    'percentage': self.config.low_conf_pct * 100,
                    'position_size': low_size,
                    'total_capital': total_low_capital,
                },
            },
            'avg_position_size': avg_position_size,
            'total_capital_deployed': total_high_capital + total_medium_capital + total_low_capital,
        }

    def print_portfolio_distribution(self, num_trades: int = 100):
        """
        Print expected portfolio distribution
        """
        dist = self.calculate_portfolio_distribution(num_trades)

        print("=" * 100)
        print(f"EXPECTED PORTFOLIO DISTRIBUTION OVER {num_trades} TRADES")
        print("=" * 100)
        print()

        print(f"{'Confidence':<12} {'# Trades':<12} {'% of Total':<12} "
              f"{'Position Size':<15} {'Total Capital':<15}")
        print("-" * 100)

        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            d = dist['distribution'][conf]
            print(f"{conf:<12} "
                  f"{d['count']:<12} "
                  f"{d['percentage']:<11.1f}% "
                  f"${d['position_size']:<14.2f} "
                  f"${d['total_capital']:<14.2f}")

        print("-" * 100)
        print(f"{'TOTAL':<12} "
              f"{dist['total_trades']:<12} "
              f"{'100.0%':<12} "
              f"${dist['avg_position_size']:<14.2f} "
              f"${dist['total_capital_deployed']:<14.2f}")

        print()
        print(f"Average Position Size: ${dist['avg_position_size']:.2f}")
        print(f"Capital Turnover: {dist['total_capital_deployed'] / self.config.total_capital:.2f}x")
        print()
        print("=" * 100)

    def generate_practical_examples(self):
        """
        Generate practical trading examples
        """
        print("\n" + "=" * 100)
        print("PRACTICAL TRADING EXAMPLES - $1,000 Portfolio")
        print("=" * 100)
        print()

        examples = [
            {
                'name': 'Example 1: High Confidence BTC Long (No Leverage)',
                'confidence': 'HIGH',
                'leverage': 1,
                'current_exposure': 0,
                'is_correlated': False,
                'entry_price': 45000,
            },
            {
                'name': 'Example 2: Medium Confidence ETH Short (2x Leverage)',
                'confidence': 'MEDIUM',
                'leverage': 2,
                'current_exposure': 0,
                'is_correlated': False,
                'entry_price': 2500,
            },
            {
                'name': 'Example 3: High Confidence SOL Long (5x Leverage)',
                'confidence': 'HIGH',
                'leverage': 5,
                'current_exposure': 0,
                'is_correlated': False,
                'entry_price': 100,
            },
            {
                'name': 'Example 4: High Confidence DeFi Token (Correlated with existing ETH position)',
                'confidence': 'HIGH',
                'leverage': 1,
                'current_exposure': 0,
                'is_correlated': True,
                'entry_price': 50,
            },
        ]

        for ex in examples:
            print(f"\n{ex['name']}")
            print("-" * 100)

            position = self.calculate_position_with_leverage(
                confidence=ex['confidence'],
                leverage=ex['leverage'],
                current_exposure=ex['current_exposure'],
                is_correlated=ex['is_correlated']
            )

            if position['allowed']:
                print(f"  Confidence Level:        {ex['confidence']}")
                print(f"  Leverage:                {ex['leverage']}x")
                print(f"  Entry Price:             ${ex['entry_price']:,.2f}")
                print(f"  Position Size:           ${position['position_size']:,.2f}")
                print(f"  Margin Required:         ${position['margin_required']:,.2f}")
                print(f"  Quantity:                {position['position_size'] / ex['entry_price']:.4f} units")
                print(f"  Stop Loss:               {position['stop_loss_pct']:.1f}%")
                print(f"  Risk Amount:             ${position['risk_amount']:.2f}")
                print(f"  Risk % of Portfolio:     {position['risk_pct_of_capital']:.2f}%")

                # Calculate stop loss price
                stop_loss_price = ex['entry_price'] * (1 - position['stop_loss_pct'] / 100)
                print(f"  Stop Loss Price:         ${stop_loss_price:,.2f}")

            else:
                print(f"  ❌ POSITION NOT ALLOWED")
                print(f"  Reason: {position['reason']}")

        print("\n" + "=" * 100)

    def export_sizing_table(self, filename: str = "position_sizing.json"):
        """Export position sizing table to JSON"""
        table = self.generate_position_sizing_table()
        distribution = self.calculate_portfolio_distribution(100)

        export_data = {
            'portfolio_capital': self.config.total_capital,
            'position_sizing_table': table,
            'expected_distribution': distribution,
            'configuration': {
                'high_kelly': self.config.high_conf_kelly,
                'medium_kelly': self.config.medium_conf_kelly,
                'low_kelly': self.config.low_conf_kelly,
                'max_position_pct': self.config.max_position_pct,
                'max_total_exposure_pct': self.config.max_total_exposure_pct,
                'stop_loss_pct': self.config.stop_loss_pct,
            }
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Position sizing table exported to {filename}")


def main():
    """Main function to run position sizing calculator"""
    print("\n" + "=" * 100)
    print("KELLY CRITERION POSITION SIZING CALCULATOR")
    print("=" * 100)
    print()

    # Initialize with $1,000 portfolio
    config = PortfolioConfig(total_capital=1000.0)
    calculator = PositionSizingCalculator(config)

    # Print position sizing table
    calculator.print_position_sizing_table()

    print("\n")
    input("Press Enter to see portfolio distribution...")

    # Print expected distribution
    calculator.print_portfolio_distribution(num_trades=100)

    print("\n")
    input("Press Enter to see practical examples...")

    # Generate practical examples
    calculator.generate_practical_examples()

    # Export to JSON
    calculator.export_sizing_table("position_sizing_1000.json")


if __name__ == "__main__":
    main()
