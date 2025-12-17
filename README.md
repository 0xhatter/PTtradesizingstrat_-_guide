# Trading Strategy Analysis - Kelly Criterion & Monte Carlo Simulation

Comprehensive toolkit for analyzing trading strategy performance using Kelly Criterion position sizing and Monte Carlo simulation.

## 📋 Overview

This toolkit provides:

1. **Kelly Criterion Position Sizing** - Optimal bet sizing based on historical win rates and reward-to-risk ratios
2. **Monte Carlo Simulation** - Stress-testing strategy performance across 10,000+ simulated scenarios
3. **Risk Analysis** - Drawdown analysis, loss streak projections, and probability of ruin
4. **Visualization** - Charts and graphs showing expected outcomes and risk metrics

## 🎯 Key Features

### Position Sizing Calculator

- Calculate optimal position sizes based on Kelly Criterion
- Separate sizing for HIGH, MEDIUM, and LOW confidence trades
- Built-in risk constraints (max position size, correlation adjustments)
- Support for leveraged positions (1x - 20x)
- Margin requirement calculations

### Monte Carlo Simulator

- Run 10,000+ simulations of 1,000 trades each
- Model realistic win/loss distributions by confidence level
- Account for slippage, commissions, and trading costs
- Generate probability distributions for expected outcomes
- Stress test with various scenarios (lower win rate, different Kelly fractions, etc.)

### Visualization & Analysis

- Equity curve projections
- Drawdown distributions
- Risk-return scatter plots
- Percentile analysis
- Summary reports in text and JSON formats

## 📊 Current Strategy Statistics

Based on 35 closed trades:

- **Win Rate**: 54.3% (19W / 16L)
- **Average Win**: $6.88
- **Average Loss**: $1.57
- **Reward-to-Risk Ratio**: 4.38:1
- **Profit Factor**: 5.20

### Performance by Confidence Level

| Confidence | Trades | PnL | Est. Win Rate |
|------------|--------|-----|---------------|
| HIGH | 24 | $93.90 | ~62.5% |
| MEDIUM | 10 | $11.16 | ~50% |
| LOW | 1 | $0.50 | ~45% |

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install numpy pandas matplotlib seaborn

# Or use requirements.txt
pip install -r requirements.txt
```

### Run Complete Analysis

```bash
# Run with default $1,000 portfolio
python run_complete_analysis.py

# Run with custom portfolio size
python run_complete_analysis.py --portfolio 5000

# Run with fewer simulations (faster)
python run_complete_analysis.py --simulations 5000

# Skip visualizations (if matplotlib not available)
python run_complete_analysis.py --no-viz
```

### Run Individual Components

```bash
# Position sizing calculator only
python position_sizing_calculator.py

# Monte Carlo simulation only
python monte_carlo_simulator.py

# Generate visualizations from existing results
python visualizations.py
```

## 📈 Position Sizing for $1,000 Portfolio

### Recommended Position Sizes (No Leverage)

| Confidence | Kelly % | Position Size | Risk per Trade |
|------------|---------|---------------|----------------|
| **HIGH** | 14.6% | $146 | ~$2.92 (2%) |
| **MEDIUM** | 11.0% | $110 | ~$2.20 (2%) |
| **LOW** | 5.5% | $55 | ~$1.10 (2%) |

### With Leverage

| Confidence | Leverage | Position Size | Margin Required |
|------------|----------|---------------|-----------------|
| HIGH | 5x | $730 | $146 |
| HIGH | 10x | $1,460 | $146 |
| MEDIUM | 5x | $550 | $110 |
| MEDIUM | 10x | $1,100 | $110 |

### Expected Distribution Over 100 Trades

Based on historical confidence distribution (67% HIGH, 31% MEDIUM, 2% LOW):

- **67 HIGH confidence trades** @ $146 each = $9,782 total deployment
- **31 MEDIUM confidence trades** @ $110 each = $3,410 total deployment
- **2 LOW confidence trades** @ $55 each = $110 total deployment

**Average position size**: ~$133 per trade

## 🎲 Monte Carlo Simulation Results

### Expected Outcomes (10,000 simulations × 1,000 trades)

**Starting Capital**: $1,000

| Metric | Conservative (25th) | Expected (50th) | Optimistic (75th) |
|--------|-------------------|-----------------|-------------------|
| **Final Capital** | ~$1,800 | ~$3,000 | ~$5,500 |
| **Total PnL** | ~$800 | ~$2,000 | ~$4,500 |
| **ROI** | 80% | 200% | 450% |
| **Max Drawdown** | 15% | 22% | 32% |

### Risk Metrics

- **Probability of Profit**: ~85-90%
- **Probability of Ruin** (<50% of capital): ~2-5%
- **Expected Max Loss Streak**: 8-12 trades
- **Worst Case Loss Streak (95th percentile)**: 15-18 trades

### Key Insights

1. **Median outcome**: ~$2,000 profit (200% ROI) over 1,000 trades
2. **5th percentile**: Still profitable (~$500+), showing robust edge
3. **95th percentile**: Exceptional (~$8,000+), demonstrating upside potential
4. **Typical drawdown**: 15-25%, manageable with proper risk controls
5. **Win rate stability**: Converges to ~54% across simulations

## 📁 Output Files

### JSON Files

- `position_sizing_1000.json` - Position sizing tables and configurations
- `monte_carlo_results.json` - Full simulation results with sample equity curves

### Visualizations

- `simulation_analysis.png` - Comprehensive 6-panel analysis dashboard
- `percentile_comparison.png` - Detailed percentile comparisons
- `simulation_summary.txt` - Text-based summary report

## 🔧 Customization

### Adjust Kelly Fractions

Edit configuration in `run_complete_analysis.py`:

```python
# More conservative (reduce volatility)
high_conf_kelly = 0.073   # 1/6 Kelly instead of 1/3
medium_conf_kelly = 0.055  # 1/8 Kelly instead of 1/4

# More aggressive (increase returns and risk)
high_conf_kelly = 0.220    # 1/2 Kelly
medium_conf_kelly = 0.146  # 1/3 Kelly
```

### Modify Risk Constraints

Edit `PortfolioConfig` in `position_sizing_calculator.py`:

```python
max_position_pct = 0.15        # Max 15% per trade (vs 20% default)
max_total_exposure_pct = 1.25  # Max 125% total (vs 150% default)
stop_loss_pct = 0.015          # 1.5% stop loss (vs 2% default)
```

### Run Different Scenarios

```python
# Test with different win rates
stats = TradeStats()
stats.win_rate = 0.50  # Test with 50% win rate

# Test with higher costs
config = SimulationConfig()
config.slippage_pct = 0.01     # 1% slippage
config.commission_pct = 0.002  # 0.2% commission
```

## ⚠️ Important Considerations

### Risk Warnings

1. **Past performance ≠ future results** - 35 trades is a small sample size
2. **Kelly sizing is aggressive** - Consider fractional Kelly (1/4 to 1/2)
3. **Compounding assumptions** - Real-world constraints limit extreme growth
4. **Model assumptions** - Simulation assumes independent, identically distributed trades

### Best Practices

1. **Start conservative** - Use 1/4 to 1/3 Kelly initially
2. **Monitor actual vs expected** - Track real performance against projections
3. **Adjust for correlation** - Reduce size when opening correlated positions
4. **Respect stop losses** - 2% stop loss is critical to risk management
5. **Scale gradually** - Increase position sizes as confidence grows

### Realistic Expectations

For a $1,000 starting portfolio:

- **Conservative target**: $1,500-2,000 (50-100% ROI) over 1,000 trades
- **Realistic target**: $2,000-3,500 (100-250% ROI) with disciplined execution
- **Optimistic scenario**: $3,500-5,000 (250-400% ROI) with favorable conditions

Timeline: 1,000 trades ≈ 1 year at ~3 trades/day

## 📚 Methodology

### Kelly Criterion

The Kelly Criterion maximizes long-term growth rate:

```
Kelly % = (Win_Rate × Avg_Win - Loss_Rate × Avg_Loss) / Avg_Win
```

For this strategy:
```
Kelly % = (0.543 × 6.88 - 0.457 × 1.57) / 6.88 = 43.9%
```

**Full Kelly is too aggressive**, so we use fractional Kelly:
- HIGH confidence: 1/3 Kelly = 14.6%
- MEDIUM confidence: 1/4 Kelly = 11.0%
- LOW confidence: 1/8 Kelly = 5.5%

### Monte Carlo Simulation

Simulates 10,000+ independent "universes" where:

1. Each universe runs 1,000 trades
2. Trade confidence is randomly assigned (67% HIGH, 31% MEDIUM, 2% LOW)
3. Win/loss outcome is sampled from historical distributions
4. PnL is sampled with realistic variance (log-normal distribution)
5. Position sizing follows Kelly Criterion with risk constraints
6. Costs (slippage, commissions) are applied to each trade

Results show the **distribution of possible outcomes** rather than a single projection.

### Laplace Succession Rule

Adjusts win rate estimates for small sample sizes:

```
Adjusted_Win_Rate = (Wins + 1) / (Total_Trades + 2)
                  = (19 + 1) / (35 + 2) = 54.05%
```

This provides a more conservative, Bayesian-adjusted estimate.

## 🤝 Contributing

Suggestions for improvements:

1. Add support for different asset classes
2. Implement volatility-based position sizing
3. Add portfolio correlation analysis
4. Create interactive dashboards
5. Add backtesting on historical data

## 📄 License

MIT License - Free to use and modify

## 📧 Support

For questions or issues, please open an issue on GitHub.

---

**Disclaimer**: This tool is for educational purposes only. Trading involves substantial risk of loss. Always do your own research and never risk more than you can afford to lose.
