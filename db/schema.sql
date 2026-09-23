-- ============================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE
-- SQLite Database Schema
-- Sprint 1 - Day 04
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- DROP TABLES
-- ============================================================

DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS companies;


-- ============================================================
-- 1. COMPANIES
-- ============================================================

CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);


-- ============================================================
-- 2. PROFIT AND LOSS
-- ============================================================

CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);


-- ============================================================
-- 3. BALANCE SHEET
-- ============================================================

CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);


-- ============================================================
-- 4. CASH FLOW
-- ============================================================

CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);


-- ============================================================
-- 5. ANALYSIS
-- ============================================================

CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);


-- ============================================================
-- 6. DOCUMENTS
-- ============================================================

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    annual_report TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);


-- ============================================================
-- 7. PROS AND CONS
-- ============================================================

CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);


-- ============================================================
-- 8. SECTORS
-- ============================================================

CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);


-- ============================================================
-- 9. STOCK PRICES
-- ============================================================

CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    adjusted_close REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, date)
);


-- ============================================================
-- 10. FINANCIAL RATIOS
-- ============================================================

CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);


-- ============================================================
-- 11. PEER GROUPS
-- ============================================================

CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER DEFAULT 0,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_profitandloss_company
ON profitandloss(company_id);

CREATE INDEX idx_balancesheet_company
ON balancesheet(company_id);

CREATE INDEX idx_cashflow_company
ON cashflow(company_id);

CREATE INDEX idx_analysis_company
ON analysis(company_id);

CREATE INDEX idx_documents_company
ON documents(company_id);

CREATE INDEX idx_prosandcons_company
ON prosandcons(company_id);

CREATE INDEX idx_sectors_company
ON sectors(company_id);

CREATE INDEX idx_stock_prices_company
ON stock_prices(company_id);

CREATE INDEX idx_financial_ratios_company
ON financial_ratios(company_id);

CREATE INDEX idx_peer_groups_company
ON peer_groups(company_id);

-- ============================================================
-- END OF SCHEMA
-- ============================================================