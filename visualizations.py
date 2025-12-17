"""
Visualization tools for Monte Carlo simulation results
Creates charts and plots for strategy performance analysis
"""

import numpy as np
import json
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import seaborn as sns


class SimulationVisualizer:
    """
    Create visualizations from Monte Carlo simulation results
    """

    def __init__(self, results_file: str = "monte_carlo_results.json"):
        """
        Initialize visualizer with results file

        Args:
            results_file: Path to JSON results file
        """
        with open(results_file, 'r') as f:
            self.data = json.load(f)

        self.analysis = self.data['analysis']
        self.config = self.data['config']
        self.sample_curves = self.data['sample_equity_curves']

        # Set style
        sns.set_style("darkgrid")
        plt.rcParams['figure.figsize'] = (16, 10)
        plt.rcParams['font.size'] = 10

    def plot_comprehensive_analysis(self, save_path: str = "simulation_analysis.png"):
        """
        Create comprehensive multi-panel visualization
        """
        fig = plt.figure(figsize=(20, 12))
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Final Capital Distribution (Histogram)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_final_capital_distribution(ax1)

        # 2. Key Metrics Summary (Text box)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_metrics_summary(ax2)

        # 3. Sample Equity Curves
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_sample_equity_curves(ax3)

        # 4. Drawdown Distribution
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_drawdown_distribution(ax4)

        # 5. PnL Distribution Box Plot
        ax5 = fig.add_subplot(gs[2, 1])
        self._plot_pnl_boxplot(ax5)

        # 6. Risk-Return Scatter
        ax6 = fig.add_subplot(gs[2, 2])
        self._plot_risk_return_scatter(ax6)

        plt.suptitle(
            f"Monte Carlo Simulation Analysis - {self.config['num_simulations']:,} Simulations × "
            f"{self.config['num_trades']} Trades",
            fontsize=16,
            fontweight='bold',
            y=0.995
        )

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Comprehensive analysis saved to {save_path}")

        return fig

    def _plot_final_capital_distribution(self, ax):
        """Plot histogram of final capital outcomes"""
        # Extract percentile data
        percentiles = self.analysis['final_capital']['percentiles']
        mean = self.analysis['final_capital']['mean']
        median = self.analysis['final_capital']['median']

        # Create histogram data (we don't have raw data, so we'll create from percentiles)
        # This is an approximation
        values = []
        prev_pct = 0
        prev_val = self.analysis['final_capital']['min']

        for pct in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            val = percentiles[pct]
            # Interpolate values between percentiles
            n_samples = int((pct - prev_pct) * self.config['num_simulations'] / 100)
            values.extend(np.linspace(prev_val, val, n_samples))
            prev_pct = pct
            prev_val = val

        # Add remaining to max
        n_remaining = self.config['num_simulations'] - len(values)
        values.extend(np.linspace(prev_val, self.analysis['final_capital']['max'], n_remaining))

        values = np.array(values)

        # Plot histogram
        ax.hist(values, bins=50, alpha=0.7, color='steelblue', edgecolor='black')

        # Add vertical lines for key metrics
        ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: ${mean:,.0f}')
        ax.axvline(median, color='green', linestyle='--', linewidth=2, label=f'Median: ${median:,.0f}')
        ax.axvline(self.config['initial_capital'], color='orange', linestyle='--',
                   linewidth=2, label=f'Initial: ${self.config["initial_capital"]:,.0f}')

        ax.set_xlabel('Final Capital ($)', fontweight='bold')
        ax.set_ylabel('Frequency', fontweight='bold')
        ax.set_title('Distribution of Final Capital Outcomes', fontweight='bold', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_metrics_summary(self, ax):
        """Plot key metrics summary as text"""
        ax.axis('off')

        metrics_text = f"""
KEY PERFORMANCE METRICS

Expected Returns:
  Mean PnL:      ${self.analysis['total_pnl']['mean']:>10,.2f}
  Median PnL:    ${self.analysis['total_pnl']['median']:>10,.2f}
  ROI (Median):  {(self.analysis['total_pnl']['median']/self.config['initial_capital'])*100:>10.1f}%

Risk Metrics:
  Avg Drawdown:  {self.analysis['max_drawdown_pct']['mean']:>10.1f}%
  95th DD:       {self.analysis['max_drawdown_pct']['percentiles'][95]:>10.1f}%
  Max DD:        {self.analysis['max_drawdown_pct']['max']:>10.1f}%

Performance:
  Avg Win Rate:  {self.analysis['win_rate']['mean']*100:>10.1f}%
  Sharpe Ratio:  {self.analysis['sharpe_ratio']['mean']:>10.2f}
  Profit Factor: {self.analysis['profit_factor']['mean']:>10.2f}x

Probability:
  Of Profit:     {self.analysis['probability_of_profit']:>10.1f}%
  Of Ruin:       {self.analysis['probability_of_ruin']:>10.1f}%

Max Loss Streak: {self.analysis['longest_loss_streak']['percentiles'][95]:>9.0f} trades
        """

        ax.text(0.1, 0.95, metrics_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def _plot_sample_equity_curves(self, ax):
        """Plot sample equity curves from simulations"""
        for sample in self.sample_curves:
            equity = sample['equity_curve']
            trades = range(len(equity))
            alpha = 0.6 if sample['simulation'] == 0 else 0.3
            linewidth = 2 if sample['simulation'] == 0 else 1
            ax.plot(trades, equity, alpha=alpha, linewidth=linewidth)

        # Add initial capital line
        ax.axhline(self.config['initial_capital'], color='red', linestyle='--',
                   linewidth=1, label='Initial Capital', alpha=0.7)

        ax.set_xlabel('Trade Number', fontweight='bold')
        ax.set_ylabel('Portfolio Value ($)', fontweight='bold')
        ax.set_title('Sample Equity Curves (5 Random Simulations)', fontweight='bold', fontsize=12)
        ax.legend(['Sample Simulations', 'Initial Capital'])
        ax.grid(True, alpha=0.3)

    def _plot_drawdown_distribution(self, ax):
        """Plot distribution of maximum drawdowns"""
        percentiles_list = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = [self.analysis['max_drawdown_pct']['percentiles'][p]
                             for p in percentiles_list]

        ax.barh(percentiles_list, percentile_values, color='coral', alpha=0.7, edgecolor='black')

        ax.set_xlabel('Max Drawdown (%)', fontweight='bold')
        ax.set_ylabel('Percentile', fontweight='bold')
        ax.set_title('Maximum Drawdown Distribution', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')

        # Add value labels
        for i, (p, v) in enumerate(zip(percentiles_list, percentile_values)):
            ax.text(v + 0.5, p, f'{v:.1f}%', va='center', fontsize=8)

    def _plot_pnl_boxplot(self, ax):
        """Plot PnL distribution as box plot"""
        # Create approximate distribution from percentiles
        percentiles = self.analysis['total_pnl']['percentiles']
        pnl_data = [
            percentiles[5],
            percentiles[25],
            percentiles[50],
            percentiles[75],
            percentiles[95],
        ]

        bp = ax.boxplot([pnl_data], vert=True, patch_artist=True,
                        labels=['Total PnL'],
                        widths=0.5)

        # Color the box
        for patch in bp['boxes']:
            patch.set_facecolor('lightgreen')
            patch.set_alpha(0.7)

        # Add horizontal line at zero
        ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)

        ax.set_ylabel('Total PnL ($)', fontweight='bold')
        ax.set_title('PnL Distribution (5th-95th Percentile)', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')

        # Add annotations
        ax.text(1.15, percentiles[50], f"Median\n${percentiles[50]:,.0f}",
                va='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    def _plot_risk_return_scatter(self, ax):
        """Plot risk-return relationship"""
        # We'll create synthetic data from percentiles
        returns_pct = []
        drawdowns = []

        for p in [10, 25, 50, 75, 90]:
            ret_pct = (self.analysis['total_pnl']['percentiles'][p] /
                      self.config['initial_capital']) * 100
            dd = self.analysis['max_drawdown_pct']['percentiles'][p]
            returns_pct.append(ret_pct)
            drawdowns.append(dd)

        # Create scatter plot
        scatter = ax.scatter(drawdowns, returns_pct, s=200, c=returns_pct,
                           cmap='RdYlGn', alpha=0.7, edgecolors='black', linewidths=2)

        # Add labels for each point
        labels = ['10th', '25th', '50th', '75th', '90th']
        for i, label in enumerate(labels):
            ax.annotate(label, (drawdowns[i], returns_pct[i]),
                       xytext=(5, 5), textcoords='offset points', fontsize=9)

        ax.set_xlabel('Maximum Drawdown (%)', fontweight='bold')
        ax.set_ylabel('Return on Investment (%)', fontweight='bold')
        ax.set_title('Risk-Return Profile (by Percentile)', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('ROI (%)', fontweight='bold')

        # Add quadrant lines
        ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
        ax.axvline(20, color='black', linestyle='--', linewidth=0.5, alpha=0.3)

    def plot_percentile_comparison(self, save_path: str = "percentile_comparison.png"):
        """
        Create detailed percentile comparison chart
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        percentiles_list = [1, 5, 10, 25, 50, 75, 90, 95, 99]

        # 1. Final Capital
        ax = axes[0, 0]
        values = [self.analysis['final_capital']['percentiles'][p] for p in percentiles_list]
        ax.plot(percentiles_list, values, marker='o', linewidth=2, markersize=8, color='steelblue')
        ax.axhline(self.config['initial_capital'], color='red', linestyle='--', label='Initial Capital')
        ax.set_xlabel('Percentile', fontweight='bold')
        ax.set_ylabel('Final Capital ($)', fontweight='bold')
        ax.set_title('Final Capital by Percentile', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # 2. Total PnL
        ax = axes[0, 1]
        values = [self.analysis['total_pnl']['percentiles'][p] for p in percentiles_list]
        ax.plot(percentiles_list, values, marker='s', linewidth=2, markersize=8, color='green')
        ax.axhline(0, color='red', linestyle='--', label='Break Even')
        ax.set_xlabel('Percentile', fontweight='bold')
        ax.set_ylabel('Total PnL ($)', fontweight='bold')
        ax.set_title('Total PnL by Percentile', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # 3. Max Drawdown
        ax = axes[1, 0]
        values = [self.analysis['max_drawdown_pct']['percentiles'][p] for p in percentiles_list]
        ax.plot(percentiles_list, values, marker='^', linewidth=2, markersize=8, color='coral')
        ax.set_xlabel('Percentile', fontweight='bold')
        ax.set_ylabel('Max Drawdown (%)', fontweight='bold')
        ax.set_title('Maximum Drawdown by Percentile', fontweight='bold')
        ax.grid(True, alpha=0.3)

        # 4. Loss Streaks
        ax = axes[1, 1]
        values = [self.analysis['longest_loss_streak']['percentiles'][p] for p in percentiles_list]
        ax.plot(percentiles_list, values, marker='D', linewidth=2, markersize=8, color='orange')
        ax.set_xlabel('Percentile', fontweight='bold')
        ax.set_ylabel('Longest Loss Streak (trades)', fontweight='bold')
        ax.set_title('Longest Loss Streak by Percentile', fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.suptitle('Percentile Analysis Across Key Metrics', fontsize=16, fontweight='bold')
        plt.tight_layout()

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Percentile comparison saved to {save_path}")

        return fig

    def create_summary_report(self, save_path: str = "simulation_summary.txt"):
        """
        Create text-based summary report
        """
        report = []
        report.append("=" * 100)
        report.append("MONTE CARLO SIMULATION SUMMARY REPORT")
        report.append("=" * 100)
        report.append("")

        # Configuration
        report.append("SIMULATION CONFIGURATION")
        report.append("-" * 100)
        report.append(f"  Number of Simulations:    {self.config['num_simulations']:>10,}")
        report.append(f"  Trades per Simulation:    {self.config['num_trades']:>10,}")
        report.append(f"  Initial Capital:          ${self.config['initial_capital']:>10,.2f}")
        report.append(f"  Compounding:              {str(self.config['use_compounding']):>10}")
        report.append(f"  HIGH Confidence Kelly:    {self.config['high_conf_kelly']*100:>10.1f}%")
        report.append(f"  MEDIUM Confidence Kelly:  {self.config['medium_conf_kelly']*100:>10.1f}%")
        report.append(f"  LOW Confidence Kelly:     {self.config['low_conf_kelly']*100:>10.1f}%")
        report.append("")

        # Expected Outcomes
        report.append("EXPECTED OUTCOMES")
        report.append("-" * 100)
        report.append(f"  Mean Final Capital:       ${self.analysis['final_capital']['mean']:>10,.2f}")
        report.append(f"  Median Final Capital:     ${self.analysis['final_capital']['median']:>10,.2f}")
        report.append(f"  Mean Total PnL:           ${self.analysis['total_pnl']['mean']:>10,.2f}")
        report.append(f"  Median Total PnL:         ${self.analysis['total_pnl']['median']:>10,.2f}")
        report.append(f"  Expected ROI (Median):    {(self.analysis['total_pnl']['median']/self.config['initial_capital'])*100:>10.1f}%")
        report.append("")

        # Risk Metrics
        report.append("RISK METRICS")
        report.append("-" * 100)
        report.append(f"  Mean Max Drawdown:        {self.analysis['max_drawdown_pct']['mean']:>10.1f}%")
        report.append(f"  Median Max Drawdown:      {self.analysis['max_drawdown_pct']['median']:>10.1f}%")
        report.append(f"  Worst Drawdown (95th):    {self.analysis['max_drawdown_pct']['percentiles'][95]:>10.1f}%")
        report.append(f"  Worst Drawdown (Max):     {self.analysis['max_drawdown_pct']['max']:>10.1f}%")
        report.append(f"  Probability of Profit:    {self.analysis['probability_of_profit']:>10.1f}%")
        report.append(f"  Probability of Ruin:      {self.analysis['probability_of_ruin']:>10.1f}%")
        report.append("")

        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 100)
        report.append(f"  Average Win Rate:         {self.analysis['win_rate']['mean']*100:>10.1f}%")
        report.append(f"  Average Sharpe Ratio:     {self.analysis['sharpe_ratio']['mean']:>10.2f}")
        report.append(f"  Average Profit Factor:    {self.analysis['profit_factor']['mean']:>10.2f}x")
        report.append(f"  Avg Longest Loss Streak:  {self.analysis['longest_loss_streak']['mean']:>10.1f} trades")
        report.append(f"  95th Pctl Loss Streak:    {self.analysis['longest_loss_streak']['percentiles'][95]:>10.0f} trades")
        report.append("")

        # Percentile Analysis
        report.append("OUTCOME PERCENTILES")
        report.append("-" * 100)
        report.append(f"{'Percentile':<12} {'Final Capital':<18} {'Total PnL':<18} {'Max DD %':<12}")
        report.append("-" * 100)

        for p in [5, 10, 25, 50, 75, 90, 95]:
            fc = self.analysis['final_capital']['percentiles'][p]
            pnl = self.analysis['total_pnl']['percentiles'][p]
            dd = self.analysis['max_drawdown_pct']['percentiles'][p]
            report.append(f"{p:>2}th         ${fc:>16,.2f}  ${pnl:>16,.2f}  {dd:>10.1f}%")

        report.append("")
        report.append("=" * 100)

        # Write to file
        with open(save_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"✅ Summary report saved to {save_path}")

        return '\n'.join(report)


def main():
    """Main function to create all visualizations"""
    print("\n" + "=" * 100)
    print("SIMULATION VISUALIZATION GENERATOR")
    print("=" * 100)
    print()

    try:
        visualizer = SimulationVisualizer("monte_carlo_results.json")

        print("Creating comprehensive analysis chart...")
        visualizer.plot_comprehensive_analysis("simulation_analysis.png")

        print("\nCreating percentile comparison chart...")
        visualizer.plot_percentile_comparison("percentile_comparison.png")

        print("\nGenerating text summary report...")
        visualizer.create_summary_report("simulation_summary.txt")

        print("\n✅ All visualizations created successfully!")
        print("\nGenerated files:")
        print("  - simulation_analysis.png")
        print("  - percentile_comparison.png")
        print("  - simulation_summary.txt")

    except FileNotFoundError:
        print("❌ Error: monte_carlo_results.json not found!")
        print("Please run the Monte Carlo simulation first.")


if __name__ == "__main__":
    main()
