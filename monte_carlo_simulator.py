"""
Monte Carlo Simulator for Trading Strategy Performance
Stress-tests Kelly Criterion projections using statistical simulation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import json
from dataclasses import dataclass, asdict
from collections import defaultdict


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


@dataclass
class TradeStats:
    """Current performance statistics"""
    win_rate: float = 0.543
    avg_win: float = 6.88
    avg_loss: float = 1.57
    total_trades: int = 35
    wins: int = 19
    losses: int = 16

    # Distribution by confidence
    high_conf_trades: int = 24
    high_conf_pnl: float = 93.90
    medium_conf_trades: int = 10
    medium_conf_pnl: float = 11.16
    low_conf_trades: int = 1
    low_conf_pnl: float = 0.50

    # Distribution percentages
    high_conf_pct: float = 0.67
    medium_conf_pct: float = 0.31
    low_conf_pct: float = 0.02


@dataclass
class SimulationConfig:
    """Configuration for Monte Carlo simulation"""
    num_simulations: int = 10000
    num_trades: int = 1000
    initial_capital: float = 1000.0
    use_compounding: bool = True

    # Kelly fractions by confidence
    high_conf_kelly: float = 0.146  # 1/3 Kelly
    medium_conf_kelly: float = 0.110  # 1/4 Kelly
    low_conf_kelly: float = 0.055  # 1/8 Kelly

    # Risk constraints
    max_position_pct: float = 0.20  # Max 20% per trade
    max_total_exposure: float = 1.50  # Max 150% total exposure
    correlation_reduction: float = 0.30  # Reduce 30% for correlated positions

    # Slippage and costs
    slippage_pct: float = 0.005  # 0.5% slippage
    commission_pct: float = 0.001  # 0.1% commission per side (0.2% total)


@dataclass
class SimulationResult:
    """Results from a single simulation run"""
    final_capital: float
    total_pnl: float
    max_drawdown: float
    max_drawdown_pct: float
    longest_win_streak: int
    longest_loss_streak: int
    total_wins: int
    total_losses: int
    actual_win_rate: float
    sharpe_ratio: float
    profit_factor: float
    equity_curve: List[float]
    drawdown_curve: List[float]


class MonteCarloSimulator:
    """
    Monte Carlo simulator for trading strategy performance
    """

    def __init__(self, stats: TradeStats, config: SimulationConfig):
        self.stats = stats
        self.config = config
        self.results: List[SimulationResult] = []

    def _generate_confidence_level(self) -> str:
        """Generate confidence level based on historical distribution"""
        rand = np.random.random()
        if rand < self.stats.high_conf_pct:
            return 'HIGH'
        elif rand < self.stats.high_conf_pct + self.stats.medium_conf_pct:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_win_rate_by_confidence(self, confidence: str) -> float:
        """Get adjusted win rate by confidence level"""
        if confidence == 'HIGH':
            # Estimate: 62.5% win rate for HIGH confidence
            return 0.625
        elif confidence == 'MEDIUM':
            # Estimate: 50% win rate for MEDIUM confidence
            return 0.500
        else:
            # Conservative for LOW confidence
            return 0.450

    def _simulate_single_trade(self, confidence: str) -> Tuple[float, bool]:
        """
        Simulate a single trade outcome
        Returns: (pnl, is_winner)
        """
        win_rate = self._get_win_rate_by_confidence(confidence)
        is_winner = np.random.random() < win_rate

        if is_winner:
            # Sample from distribution around avg_win
            # Using log-normal to prevent negative values
            pnl = np.random.lognormal(
                mean=np.log(self.stats.avg_win),
                sigma=0.5  # Volatility parameter
            )
        else:
            # Sample from distribution around avg_loss
            pnl = -np.random.lognormal(
                mean=np.log(self.stats.avg_loss),
                sigma=0.4
            )

        # Apply slippage and commissions
        slippage_cost = abs(pnl) * self.config.slippage_pct
        commission_cost = abs(pnl) * self.config.commission_pct * 2  # Both sides

        pnl = pnl - slippage_cost - commission_cost

        return pnl, is_winner

    def _calculate_position_size(
        self,
        capital: float,
        confidence: str,
        risk_pct: float = 1.0
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        """
        if confidence == 'HIGH':
            kelly_fraction = self.config.high_conf_kelly
        elif confidence == 'MEDIUM':
            kelly_fraction = self.config.medium_conf_kelly
        else:
            kelly_fraction = self.config.low_conf_kelly

        # Base position size
        position_size = capital * kelly_fraction * risk_pct

        # Apply maximum position constraint
        max_position = capital * self.config.max_position_pct
        position_size = min(position_size, max_position)

        return position_size

    def _run_single_simulation(self) -> SimulationResult:
        """
        Run a single simulation of N trades
        """
        capital = self.config.initial_capital
        equity_curve = [capital]
        peak_capital = capital
        max_drawdown = 0.0

        wins = 0
        losses = 0
        current_streak = 0
        longest_win_streak = 0
        longest_loss_streak = 0
        last_trade_won = None

        gross_profit = 0.0
        gross_loss = 0.0
        returns = []

        for trade_num in range(self.config.num_trades):
            # Generate confidence level for this trade
            confidence = self._generate_confidence_level()

            # Calculate position size
            if self.config.use_compounding:
                position_size = self._calculate_position_size(capital, confidence)
            else:
                position_size = self._calculate_position_size(
                    self.config.initial_capital,
                    confidence
                )

            # Simulate trade
            pnl_per_unit, is_winner = self._simulate_single_trade(confidence)

            # Scale PnL by position size (normalized to initial capital)
            # This assumes PnL is in percentage terms
            trade_pnl = pnl_per_unit * (position_size / self.config.initial_capital)

            # Update capital
            capital += trade_pnl

            # Track metrics
            if is_winner:
                wins += 1
                gross_profit += abs(trade_pnl)
                if last_trade_won == True:
                    current_streak += 1
                else:
                    current_streak = 1
                longest_win_streak = max(longest_win_streak, current_streak)
                last_trade_won = True
            else:
                losses += 1
                gross_loss += abs(trade_pnl)
                if last_trade_won == False:
                    current_streak += 1
                else:
                    current_streak = 1
                longest_loss_streak = max(longest_loss_streak, current_streak)
                last_trade_won = False

            # Update equity curve
            equity_curve.append(capital)

            # Track drawdown
            if capital > peak_capital:
                peak_capital = capital

            drawdown = peak_capital - capital
            max_drawdown = max(max_drawdown, drawdown)

            # Calculate return for this trade
            if len(equity_curve) > 1:
                ret = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
                returns.append(ret)

            # Stop if wiped out
            if capital <= 0:
                capital = 0
                equity_curve.append(0)
                break

        # Calculate final metrics
        total_pnl = capital - self.config.initial_capital
        max_drawdown_pct = (max_drawdown / peak_capital * 100) if peak_capital > 0 else 100
        actual_win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0

        # Sharpe ratio (annualized, assuming 365 trades per year)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(365)
        else:
            sharpe_ratio = 0.0

        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Drawdown curve
        drawdown_curve = []
        peak = equity_curve[0]
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak * 100) if peak > 0 else 0
            drawdown_curve.append(dd)

        return SimulationResult(
            final_capital=capital,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
            total_wins=wins,
            total_losses=losses,
            actual_win_rate=actual_win_rate,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve
        )

    def run_simulation(self, verbose: bool = True) -> Dict:
        """
        Run Monte Carlo simulation
        """
        if verbose:
            print(f"Running {self.config.num_simulations:,} simulations...")
            print(f"Each simulation: {self.config.num_trades} trades")
            print(f"Initial capital: ${self.config.initial_capital:,.2f}")
            print(f"Compounding: {self.config.use_compounding}")
            print()

        self.results = []

        for i in range(self.config.num_simulations):
            result = self._run_single_simulation()
            self.results.append(result)

            if verbose and (i + 1) % 1000 == 0:
                print(f"  Completed {i + 1:,} simulations...")

        if verbose:
            print()

        return self.analyze_results(verbose=verbose)

    def analyze_results(self, verbose: bool = True) -> Dict:
        """
        Analyze simulation results and return statistics
        """
        # Extract metrics
        final_capitals = [r.final_capital for r in self.results]
        total_pnls = [r.total_pnl for r in self.results]
        max_drawdowns = [r.max_drawdown_pct for r in self.results]
        win_rates = [r.actual_win_rate for r in self.results]
        sharpe_ratios = [r.sharpe_ratio for r in self.results]
        profit_factors = [r.profit_factor for r in self.results if r.profit_factor != float('inf')]
        longest_loss_streaks = [r.longest_loss_streak for r in self.results]

        # Calculate percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

        analysis = {
            'final_capital': {
                'mean': np.mean(final_capitals),
                'median': np.median(final_capitals),
                'std': np.std(final_capitals),
                'min': np.min(final_capitals),
                'max': np.max(final_capitals),
                'percentiles': {p: np.percentile(final_capitals, p) for p in percentiles}
            },
            'total_pnl': {
                'mean': np.mean(total_pnls),
                'median': np.median(total_pnls),
                'std': np.std(total_pnls),
                'min': np.min(total_pnls),
                'max': np.max(total_pnls),
                'percentiles': {p: np.percentile(total_pnls, p) for p in percentiles}
            },
            'max_drawdown_pct': {
                'mean': np.mean(max_drawdowns),
                'median': np.median(max_drawdowns),
                'std': np.std(max_drawdowns),
                'min': np.min(max_drawdowns),
                'max': np.max(max_drawdowns),
                'percentiles': {p: np.percentile(max_drawdowns, p) for p in percentiles}
            },
            'win_rate': {
                'mean': np.mean(win_rates),
                'median': np.median(win_rates),
                'std': np.std(win_rates),
            },
            'sharpe_ratio': {
                'mean': np.mean(sharpe_ratios),
                'median': np.median(sharpe_ratios),
            },
            'profit_factor': {
                'mean': np.mean(profit_factors),
                'median': np.median(profit_factors),
            },
            'longest_loss_streak': {
                'mean': np.mean(longest_loss_streaks),
                'median': np.median(longest_loss_streaks),
                'max': np.max(longest_loss_streaks),
                'percentiles': {p: np.percentile(longest_loss_streaks, p) for p in percentiles}
            },
            'probability_of_profit': sum(1 for pnl in total_pnls if pnl > 0) / len(total_pnls) * 100,
            'probability_of_ruin': sum(1 for cap in final_capitals if cap < self.config.initial_capital * 0.5) / len(final_capitals) * 100,
        }

        if verbose:
            self._print_analysis(analysis)

        return analysis

    def _print_analysis(self, analysis: Dict):
        """Print formatted analysis"""
        print("=" * 80)
        print("MONTE CARLO SIMULATION RESULTS")
        print("=" * 80)
        print()

        print(f"📊 FINAL CAPITAL (Starting: ${self.config.initial_capital:,.2f})")
        print(f"  Mean:       ${analysis['final_capital']['mean']:>12,.2f}")
        print(f"  Median:     ${analysis['final_capital']['median']:>12,.2f}")
        print(f"  Std Dev:    ${analysis['final_capital']['std']:>12,.2f}")
        print(f"  Min:        ${analysis['final_capital']['min']:>12,.2f}")
        print(f"  Max:        ${analysis['final_capital']['max']:>12,.2f}")
        print()
        print(f"  Percentiles:")
        for p in [5, 25, 50, 75, 95]:
            val = analysis['final_capital']['percentiles'][p]
            print(f"    {p:>2}th:     ${val:>12,.2f}")
        print()

        print(f"💰 TOTAL PnL")
        print(f"  Mean:       ${analysis['total_pnl']['mean']:>12,.2f}")
        print(f"  Median:     ${analysis['total_pnl']['median']:>12,.2f}")
        print(f"  Std Dev:    ${analysis['total_pnl']['std']:>12,.2f}")
        print(f"  Min:        ${analysis['total_pnl']['min']:>12,.2f}")
        print(f"  Max:        ${analysis['total_pnl']['max']:>12,.2f}")
        print()
        print(f"  Percentiles:")
        for p in [5, 25, 50, 75, 95]:
            val = analysis['total_pnl']['percentiles'][p]
            print(f"    {p:>2}th:     ${val:>12,.2f}")
        print()

        print(f"📉 MAX DRAWDOWN")
        print(f"  Mean:       {analysis['max_drawdown_pct']['mean']:>12.2f}%")
        print(f"  Median:     {analysis['max_drawdown_pct']['median']:>12.2f}%")
        print(f"  Worst:      {analysis['max_drawdown_pct']['max']:>12.2f}%")
        print()
        print(f"  Percentiles:")
        for p in [50, 75, 90, 95, 99]:
            val = analysis['max_drawdown_pct']['percentiles'][p]
            print(f"    {p:>2}th:     {val:>12.2f}%")
        print()

        print(f"🎯 PERFORMANCE METRICS")
        print(f"  Avg Win Rate:           {analysis['win_rate']['mean']*100:>6.2f}%")
        print(f"  Avg Sharpe Ratio:       {analysis['sharpe_ratio']['mean']:>6.2f}")
        print(f"  Avg Profit Factor:      {analysis['profit_factor']['mean']:>6.2f}x")
        print()

        print(f"⚠️  RISK METRICS")
        print(f"  Probability of Profit:  {analysis['probability_of_profit']:>6.2f}%")
        print(f"  Probability of Ruin:    {analysis['probability_of_ruin']:>6.2f}%")
        print(f"  Max Loss Streak (avg):  {analysis['longest_loss_streak']['mean']:>6.1f} trades")
        print(f"  Max Loss Streak (95th): {analysis['longest_loss_streak']['percentiles'][95]:>6.0f} trades")
        print()

        print("=" * 80)

    def export_results(self, filename: str = "simulation_results.json"):
        """Export results to JSON"""
        analysis = self.analyze_results(verbose=False)

        export_data = {
            'config': asdict(self.config),
            'stats': asdict(self.stats),
            'analysis': analysis,
            'sample_equity_curves': [
                {
                    'simulation': i,
                    'equity_curve': self.results[i].equity_curve,
                    'drawdown_curve': self.results[i].drawdown_curve,
                    'final_capital': self.results[i].final_capital,
                }
                for i in [0, len(self.results)//4, len(self.results)//2, 3*len(self.results)//4, -1]
            ]
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, cls=NumpyEncoder)

        print(f"✅ Results exported to {filename}")


def run_standard_simulation():
    """Run standard Monte Carlo simulation with default parameters"""
    stats = TradeStats()
    config = SimulationConfig()

    simulator = MonteCarloSimulator(stats, config)
    analysis = simulator.run_simulation(verbose=True)

    # Export results
    simulator.export_results("monte_carlo_results.json")

    return simulator, analysis


def run_stress_tests():
    """Run various stress test scenarios"""
    print("\n" + "="*80)
    print("STRESS TEST SCENARIOS")
    print("="*80 + "\n")

    stats = TradeStats()
    scenarios = {
        'Conservative (No Compounding)': {
            'use_compounding': False,
        },
        'Lower Win Rate (50%)': {
            'win_rate_override': 0.50,
        },
        'Higher Slippage (1%)': {
            'slippage_pct': 0.01,
        },
        'Half Kelly (More Conservative)': {
            'high_conf_kelly': 0.073,
            'medium_conf_kelly': 0.055,
            'low_conf_kelly': 0.0275,
        },
        'Full Kelly (Aggressive)': {
            'high_conf_kelly': 0.439,
            'medium_conf_kelly': 0.330,
            'low_conf_kelly': 0.165,
        },
    }

    results = {}

    for scenario_name, overrides in scenarios.items():
        print(f"\n📋 Running: {scenario_name}")
        print("-" * 80)

        config = SimulationConfig(
            num_simulations=5000,  # Fewer for speed
            **overrides
        )

        # Handle win rate override
        if 'win_rate_override' in overrides:
            stats.win_rate = overrides['win_rate_override']

        simulator = MonteCarloSimulator(stats, config)
        analysis = simulator.run_simulation(verbose=False)

        results[scenario_name] = analysis

        print(f"  Expected Final Capital: ${analysis['final_capital']['median']:,.2f}")
        print(f"  Expected PnL:          ${analysis['total_pnl']['median']:,.2f}")
        print(f"  Median Drawdown:       {analysis['max_drawdown_pct']['median']:.2f}%")
        print(f"  Probability of Profit: {analysis['probability_of_profit']:.1f}%")

    print("\n" + "="*80)
    return results


if __name__ == "__main__":
    print("Monte Carlo Trading Strategy Simulator")
    print()

    # Run standard simulation
    simulator, analysis = run_standard_simulation()

    print("\n")
    input("Press Enter to run stress tests...")

    # Run stress tests
    stress_results = run_stress_tests()
