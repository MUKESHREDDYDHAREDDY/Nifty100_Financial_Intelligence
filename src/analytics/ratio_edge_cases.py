"""
Day 13 - Ratio Edge Case Analysis

Checks:
1. Financials high-D/E suppression
2. ROCE source cross-check
3. ROE source cross-check
4. Anomaly logging
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")
OUTPUT_PATH = Path("output/ratio_edge_cases.log")


def ensure_output_directory():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def classify_anomaly(computed, source, tolerance):
    """
    Classify source/computed differences.

    Categories:
    - data source issue
    - formula discrepancy
    """

    if computed is None or source is None:
        return "data source issue"

    difference = abs(computed - source)

    if difference > tolerance:
        return "data source issue"

    return "version difference"


def run():
    ensure_output_directory()

    conn = sqlite3.connect(DB_PATH)

    try:
        # Check that broad_sector exists.
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(companies)"
            ).fetchall()
        }

        if "broad_sector" not in columns:
            raise RuntimeError(
                "companies.broad_sector does not exist. "
                "Run sector_classification first."
            )

        financials = conn.execute(
            """
            SELECT COUNT(*)
            FROM companies
            WHERE broad_sector = 'Financials'
            """
        ).fetchone()[0]

        suppressed = conn.execute(
            """
            SELECT COUNT(*)
            FROM financial_ratios f
            JOIN companies c
              ON f.company_id = c.id
            WHERE c.broad_sector = 'Financials'
              AND f.debt_to_equity > 5
            """
        ).fetchone()[0]

        high_de = conn.execute(
            """
            SELECT COUNT(*)
            FROM financial_ratios f
            JOIN companies c
              ON f.company_id = c.id
            WHERE c.broad_sector != 'Financials'
              AND f.debt_to_equity > 5
            """
        ).fetchone()[0]

        anomalies = []

        # ---------------------------------------------------------
        # ROCE cross-check
        # ---------------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                f.company_id,
                f.year,
                f.return_on_equity_pct,
                c.roe_percentage,
                c.roce_percentage
            FROM financial_ratios f
            JOIN companies c
              ON f.company_id = c.id
            ORDER BY f.company_id, f.year
            """
        ).fetchall()

        for (
            company_id,
            year,
            computed_roe,
            source_roe,
            source_roce,
        ) in rows:

            # ROE source comparison.
            if (
                computed_roe is not None
                and source_roe is not None
            ):
                difference = abs(
                    computed_roe - source_roe
                )

                if difference > 5:
                    anomalies.append(
                        {
                            "company_id": company_id,
                            "year": year,
                            "metric": "ROE",
                            "computed": computed_roe,
                            "source": source_roe,
                            "difference": difference,
                            "category": classify_anomaly(
                                computed_roe,
                                source_roe,
                                5,
                            ),
                        }
                    )

            # -----------------------------------------------------
            # ROCE source comparison
            #
            # The current financial_ratios table does not contain
            # ROCE, so this section documents that limitation.
            # -----------------------------------------------------

        # ---------------------------------------------------------
        # Write log
        # ---------------------------------------------------------

        with OUTPUT_PATH.open(
            "w",
            encoding="utf-8",
        ) as log:

            log.write(
                "DAY 13 - RATIO EDGE CASE ANALYSIS\n"
            )
            log.write("=" * 70 + "\n\n")

            log.write(
                f"Financials companies: {financials}\n"
            )

            log.write(
                "Financials high-D/E warnings suppressed: "
                f"{suppressed}\n"
            )

            log.write(
                "Non-Financial high-D/E flags: "
                f"{high_de}\n"
            )

            log.write(
                f"ROE anomalies: {len(anomalies)}\n\n"
            )

            log.write(
                "ROCE SOURCE CROSS-CHECK\n"
            )
            log.write("-" * 70 + "\n")
            log.write(
                "ROCE cannot currently be cross-checked because "
                "return_on_capital_employed_pct is not stored in "
                "financial_ratios.\n"
            )
            log.write(
                "The source companies table contains "
                "roce_percentage.\n"
            )
            log.write(
                "Add a computed ROCE column before claiming "
                "ROCE cross-check completion.\n\n"
            )

            log.write(
                "ROE ANOMALIES\n"
            )
            log.write("-" * 70 + "\n")

            for anomaly in anomalies:
                log.write(
                    f"{anomaly['company_id']} | "
                    f"{anomaly['year']} | "
                    f"{anomaly['metric']} | "
                    f"computed={anomaly['computed']:.4f} | "
                    f"source={anomaly['source']:.4f} | "
                    f"difference={anomaly['difference']:.4f} | "
                    f"category={anomaly['category']}\n"
                )

            log.write("\n")
            log.write(
                "NOTE: Source ROE/ROCE values are retained for "
                "display/cross-checking only. Ratio-engine values "
                "are used for analytics.\n"
            )

        print("=" * 70)
        print("DAY 13 - RATIO EDGE CASE ANALYSIS")
        print("=" * 70)
        print("Financials companies:", financials)
        print(
            "Financials high-D/E warnings suppressed:",
            suppressed,
        )
        print(
            "Non-Financial high-D/E flags:",
            high_de,
        )
        print("ROE anomalies:", len(anomalies))
        print("Log created:", OUTPUT_PATH)
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    run()