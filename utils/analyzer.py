
import quantstats as qs


def show_analyzer(strat, name='pyfolio'):
    try:
        portfolio_stats = strat.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        returns.index = returns.index.tz_convert(None)

        qs.reports.html(returns, output='stats.html', title='R-Breaker策略绩效报告', rf=0.0)
        df = qs.reports.metrics(returns=returns, mode='basic',display=False)
        qs.reports.basic(returns)
    except:
        pass