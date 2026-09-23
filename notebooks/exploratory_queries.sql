-- Query 1: Top 10 companies by market capitalization
SELECT
    c.company_name,
    m.company_id,
    m.year,
    m.market_cap_crore
FROM market_cap m
JOIN companies c
    ON m.company_id = c.id
ORDER BY m.market_cap_crore DESC
LIMIT 10;

-- Query 2: Top 10 companies by Return on Equity (ROE)
SELECT
    company_name,
    id AS company_id,
    roe_percentage
FROM companies
WHERE roe_percentage IS NOT NULL
ORDER BY roe_percentage DESC
LIMIT 10;

-- Query 3: Top 10 companies by net profit
SELECT
    c.company_name,
    p.company_id,
    p.year,
    p.net_profit
FROM profitandloss p
JOIN companies c
    ON p.company_id = c.id
WHERE p.net_profit IS NOT NULL
ORDER BY p.net_profit DESC
LIMIT 10;

-- Query 4: Companies with negative net profit
SELECT
    c.company_name,
    p.company_id,
    p.year,
    p.net_profit
FROM profitandloss p
JOIN companies c
    ON p.company_id = c.id
WHERE p.net_profit < 0
ORDER BY p.net_profit ASC
LIMIT 10;

-- Query 5: Top 10 companies by operating profit margin
SELECT
    c.company_name,
    p.company_id,
    p.year,
    p.opm_percentage
FROM profitandloss p
JOIN companies c
    ON p.company_id = c.id
WHERE p.opm_percentage IS NOT NULL
ORDER BY p.opm_percentage DESC
LIMIT 10;
-- Query 6: Number of companies in each broad sector
SELECT
    broad_sector,
    COUNT(*) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_index_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- Query 7: Companies with the highest debt-to-equity ratio
SELECT
    c.company_name,
    f.company_id,
    f.year,
    f.debt_to_equity
FROM financial_ratios f
JOIN companies c
    ON f.company_id = c.id
WHERE f.debt_to_equity IS NOT NULL
ORDER BY f.debt_to_equity DESC
LIMIT 10;

-- Query 8: Top 10 companies by free cash flow
SELECT
    c.company_name,
    f.company_id,
    f.year,
    f.free_cash_flow_cr
FROM financial_ratios f
JOIN companies c
    ON f.company_id = c.id
WHERE f.free_cash_flow_cr IS NOT NULL
ORDER BY f.free_cash_flow_cr DESC
LIMIT 10;

-- Query 9: Top 10 companies by dividend yield
SELECT
    c.company_name,
    m.company_id,
    m.year,
    m.dividend_yield_pct
FROM market_cap m
JOIN companies c
    ON m.company_id = c.id
WHERE m.dividend_yield_pct IS NOT NULL
ORDER BY m.dividend_yield_pct DESC
LIMIT 10;

SELECT
    c.company_name,
    m.company_id,
    m.year,
    m.dividend_yield_pct
FROM market_cap m
JOIN companies c
    ON m.company_id = c.id
WHERE m.dividend_yield_pct IS NOT NULL
ORDER BY m.dividend_yield_pct DESC
LIMIT 10;