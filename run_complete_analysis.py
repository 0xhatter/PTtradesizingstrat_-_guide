#!/usr/bin/env python3
"""
Complete Trading Strategy Analysis Runner
Runs Monte Carlo simulations, position sizing analysis, and generates visualizations
"""

import sys
import argparse
from monte_carlo_simulator import (
    MonteCarloSimulator,
    TradeStats,
    SimulationConfig,
    run_standard_simulation,
    run_stress_tests
)
from position_sizing_calculator import (
    PositionSizingCalculator,
    PortfolioConfig
)


def run_full_analysis(
    portfolio_size: float = 1000.0,
    num_simulations: int = 10000,
    num_trades: int = 1000,
    skip_visualization: bool = False
):
    """
    Run complete trading strategy analysis

    Args:
        portfolio_size: Starting portfolio size in dollars
        num_simulations: Number of Monte Carlo simulations to run
        num_trades: Number of trades per simulation
        skip_visualization: Skip creating visualization (useful if matplotlib not available)
    """
    print("\n" + "="*100)
    print("COMPLETE TRADING STRATEGY ANALYSIS")
    print("="*100)
    print()
    print(f"Portfolio Size:      ${portfolio_size:,.2f}")
    print(f"Simulations:         {num_simulations:,}")
    print(f"Trades per Sim:      {num_trades:,}")
    print()
    print("="*100)
    print()

    # PART 1: Position Sizing Analysis
    print("\n" + "="*100)
    print("PART 1: POSITION SIZING ANALYSIS")
    print("="*100)
    print()

    config = PortfolioConfig(total_capital=portfolio_size)
    calculator = PositionSizingCalculator(config)

    print("1.1: Position Sizing Table")
    print("-"*100)
    calculator.print_position_sizing_table()

    print("\n\n1.2: Expected Portfolio Distribution")
    print("-"*100)
    calculator.print_portfolio_distribution(num_trades=100)

    print("\n\n1.3: Practical Trading Examples")
    print("-"*100)
    calculator.generate_practical_examples()

    # Export position sizing
    calculator.export_sizing_table(f"position_sizing_{int(portfolio_size)}.json")

    # PART 2: Monte Carlo Simulation
    print("\n\n" + "="*100)
    print("PART 2: MONTE CARLO SIMULATION")
    print("="*100)
    print()

    stats = TradeStats()
    sim_config = SimulationConfig(
        num_simulations=num_simulations,
        num_trades=num_trades,
        initial_capital=portfolio_size,
        use_compounding=True
    )

    print(f"Running {num_simulations:,} simulations of {num_trades} trades each...")
    print(f"This may take a few minutes...\n")

    simulator = MonteCarloSimulator(stats, sim_config)
    analysis = simulator.run_simulation(verbose=True)

    # Export results
    simulator.export_results("monte_carlo_results.json")

    # PART 3: Stress Testing
    print("\n\n" + "="*100)
    print("PART 3: STRESS TEST SCENARIOS")
    print("="*100)
    print()

    print("Running stress tests with various parameter modifications...")
    print()

    # Run simplified stress tests
    stress_scenarios = {
        'Conservative (No Compounding)': {
            'use_compounding': False,
        },
        'Lower Win Rate (50%)': {
            'use_compounding': True,
        },
        'Half Kelly Sizing': {
            'high_conf_kelly': 0.073,
            'medium_conf_kelly': 0.055,
            'low_conf_kelly': 0.0275,
        },
    }

    stress_results = {}

    for scenario_name, overrides in stress_scenarios.items():
        print(f"\n📋 {scenario_name}")
        print("-" * 100)

        test_config = SimulationConfig(
            num_simulations=min(5000, num_simulations),  # Use fewer for speed
            num_trades=num_trades,
            initial_capital=portfolio_size,
            **overrides
        )

        test_stats = stats
        if 'Lower Win Rate' in scenario_name:
            test_stats = TradeStats()
            test_stats.win_rate = 0.50

        test_sim = MonteCarloSimulator(test_stats, test_config)
        test_analysis = test_sim.run_simulation(verbose=False)

        stress_results[scenario_name] = test_analysis

        print(f"  Expected Final Capital: ${test_analysis['final_capital']['median']:,.2f}")
        print(f"  Expected PnL:          ${test_analysis['total_pnl']['median']:,.2f}")
        print(f"  Median Drawdown:       {test_analysis['max_drawdown_pct']['median']:.2f}%")
        print(f"  Probability of Profit: {test_analysis['probability_of_profit']:.1f}%")

    # PART 4: Visualization
    if not skip_visualization:
        print("\n\n" + "="*100)
        print("PART 4: GENERATING VISUALIZATIONS")
        print("="*100)
        print()

        try:
            from visualizations import SimulationVisualizer
            visualizer = SimulationVisualizer("monte_carlo_results.json")

            print("Creating comprehensive analysis chart...")
            visualizer.plot_comprehensive_analysis("simulation_analysis.png")

            print("Creating percentile comparison chart...")
            visualizer.plot_percentile_comparison("percentile_comparison.png")

            print("Generating text summary report...")
            visualizer.create_summary_report("simulation_summary.txt")

            print("\n✅ All visualizations created successfully!")

        except ImportError as e:
            print(f"⚠️  Visualization skipped: {e}")
            print("   Install matplotlib and seaborn to enable visualizations:")
            print("   pip install matplotlib seaborn")
        except Exception as e:
            print(f"❌ Error creating visualizations: {e}")

    # PART 5: Summary and Recommendations
    print("\n\n" + "="*100)
    print("FINAL SUMMARY AND RECOMMENDATIONS")
    print("="*100)
    print()

    median_pnl = analysis['total_pnl']['median']
    median_final = analysis['final_capital']['median']
    roi = (median_pnl / portfolio_size) * 100
    median_dd = analysis['max_drawdown_pct']['median']
    prob_profit = analysis['probability_of_profit']

    print(f"📊 EXPECTED OUTCOMES (Median Case)")
    print(f"   Starting Capital:    ${portfolio_size:,.2f}")
    print(f"   Expected Final:      ${median_final:,.2f}")
    print(f"   Expected Profit:     ${median_pnl:,.2f}")
    print(f"   Expected ROI:        {roi:.1f}%")
    print()

    print(f"⚠️  RISK ASSESSMENT")
    print(f"   Expected Max Drawdown:   {median_dd:.1f}%")
    print(f"   Worst Case DD (95th):    {analysis['max_drawdown_pct']['percentiles'][95]:.1f}%")
    print(f"   Probability of Profit:   {prob_profit:.1f}%")
    print(f"   Expected Loss Streaks:   {analysis['longest_loss_streak']['mean']:.0f} trades (avg)")
    print()

    print(f"💡 POSITION SIZING RECOMMENDATIONS")
    print(f"   HIGH Confidence:     ${calculator.calculate_base_position_size('HIGH'):.2f} per trade")
    print(f"   MEDIUM Confidence:   ${calculator.calculate_base_position_size('MEDIUM'):.2f} per trade")
    print(f"   LOW Confidence:      ${calculator.calculate_base_position_size('LOW'):.2f} per trade")
    print()

    print(f"📈 PERFORMANCE OUTLOOK")
    if roi > 200:
        print(f"   ✅ EXCELLENT: {roi:.0f}% ROI is exceptional")
    elif roi > 100:
        print(f"   ✅ VERY GOOD: {roi:.0f}% ROI is strong")
    elif roi > 50:
        print(f"   ✅ GOOD: {roi:.0f}% ROI is solid")
    elif roi > 0:
        print(f"   ⚠️  MODEST: {roi:.0f}% ROI is positive but modest")
    else:
        print(f"   ❌ NEGATIVE: Expected loss of {abs(roi):.0f}%")

    print()

    if median_dd < 15:
        print(f"   ✅ LOW RISK: {median_dd:.1f}% drawdown is manageable")
    elif median_dd < 30:
        print(f"   ⚠️  MODERATE RISK: {median_dd:.1f}% drawdown requires discipline")
    else:
        print(f"   ❌ HIGH RISK: {median_dd:.1f}% drawdown is substantial")

    print()

    print("📁 GENERATED FILES:")
    print(f"   - position_sizing_{int(portfolio_size)}.json")
    print(f"   - monte_carlo_results.json")
    if not skip_visualization:
        print(f"   - simulation_analysis.png")
        print(f"   - percentile_comparison.png")
        print(f"   - simulation_summary.txt")

    print()
    print("="*100)
    print("ANALYSIS COMPLETE!")
    print("="*100)


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Complete Trading Strategy Analysis with Monte Carlo Simulation'
    )

    parser.add_argument(
        '--portfolio',
        type=float,
        default=1000.0,
        help='Starting portfolio size in dollars (default: 1000)'
    )

    parser.add_argument(
        '--simulations',
        type=int,
        default=10000,
        help='Number of Monte Carlo simulations (default: 10000)'
    )

    parser.add_argument(
        '--trades',
        type=int,
        default=1000,
        help='Number of trades per simulation (default: 1000)'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization generation'
    )

    args = parser.parse_args()

    run_full_analysis(
        portfolio_size=args.portfolio,
        num_simulations=args.simulations,
        num_trades=args.trades,
        skip_visualization=args.no_viz
    )


if __name__ == "__main__":
    main()
