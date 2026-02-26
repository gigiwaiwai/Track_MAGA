import os
import sys
from datetime import date
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Ensure stdout handles UTF-8 (needed on Windows with cp1252 terminals)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TICKERS = {
    "10Y Yield (TNX)": "^TNX",
    "DXY": "DX-Y.NYB",
    "5Y Yield (FVX)": "^FVX",
    "VIX": "^VIX",
    "Nasdaq": "^IXIC",
    "BTC": "BTC-USD",
}

ORDER = ["10Y Yield (TNX)", "DXY", "5Y Yield (FVX)", "VIX", "Nasdaq", "BTC"]


def fetch_series(ticker):
    try:
        df = yf.download(ticker, period="13mo", auto_adjust=True, progress=False)
        s = df["Close"].squeeze().dropna()
        if len(s) < 2:
            return None
        return s
    except Exception:
        return None


def pct_change(series, days):
    if len(series) < days + 1:
        return None
    return (series.iloc[-1] - series.iloc[-(days + 1)]) / series.iloc[-(days + 1)] * 100


def trend(ret20):
    if ret20 is None:
        return "N/A"
    if ret20 > 2:
        return "up"
    if ret20 < -2:
        return "down"
    return "sideways"


def fmt_pct(v):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%"


def fmt_price(name, value):
    if "Yield" in name or name == "VIX":
        return f"{value:.2f}%"
    if "BTC" in name:
        return f"{value:,.1f}"
    return f"{value:.1f}"


def plot_panel(ax, series, n_days, name):
    """Plot a single price history panel on the given axes."""
    sub = series.iloc[-n_days:]
    if len(sub) < 2:
        ax.text(0.5, 0.5, "N/A", ha="center", va="center", transform=ax.transAxes)
        return

    dates = sub.index.to_pydatetime()
    vals = sub.values.astype(float)

    color = "#27ae60" if vals[-1] >= vals[0] else "#e74c3c"

    ax.plot(dates, vals, color=color, linewidth=1.5)
    ax.fill_between(dates, vals, vals.min(), alpha=0.12, color=color)

    # Dashed baseline at period-start value
    ax.axhline(vals[0], color="gray", linewidth=0.8, linestyle="--", alpha=0.5)

    # Date formatting
    if n_days <= 31:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)

    # Stats text box
    delta_pct = (vals[-1] - vals[0]) / vals[0] * 100
    sign = "+" if delta_pct >= 0 else ""
    hi_val = fmt_price(name, vals.max())
    lo_val = fmt_price(name, vals.min())
    cur_val = fmt_price(name, vals[-1])
    stats = f"{cur_val}  {sign}{delta_pct:.1f}%\nhi {hi_val}  lo {lo_val}"
    ax.text(
        0.02, 0.97, stats,
        transform=ax.transAxes,
        fontsize=7,
        verticalalignment="top",
        bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="none"),
    )

    # Clean spines and grid
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_tick_params(labelsize=7)
    ax.grid(True, alpha=0.25)


def save_charts(today_str, data, out_path):
    """Generate a 6×2 PDF chart (1M left, 1Y right) for all indicators."""
    fig, axes = plt.subplots(6, 2, figsize=(13, 18))
    fig.suptitle(f"Macro Snapshot — {today_str}", fontsize=14, fontweight="bold", y=0.995)

    # Column headers
    axes[0, 0].set_title("1 Month", fontsize=10, fontweight="bold")
    axes[0, 1].set_title("1 Year", fontsize=10, fontweight="bold")

    for row, name in enumerate(ORDER):
        s = data.get(name)
        axes[row, 0].set_ylabel(name, fontsize=8, labelpad=4)

        if s is None:
            for col in (0, 1):
                axes[row, col].text(
                    0.5, 0.5, "N/A", ha="center", va="center",
                    transform=axes[row, col].transAxes
                )
            continue

        plot_panel(axes[row, 0], s, n_days=22,  name=name)
        plot_panel(axes[row, 1], s, n_days=252, name=name)

    fig.tight_layout(rect=[0, 0, 1, 0.995])
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def build_report(today_str, data):
    lines = []
    lines.append(f"# Macro Snapshot - {today_str}")
    lines.append("")

    # ── Indicators ──────────────────────────────────────────────────────────
    lines.append("## Indicators")
    lines.append("")

    for name in ORDER:
        s = data.get(name)
        if s is None:
            lines.append(f"**{name}**: N/A")
            continue
        price = s.iloc[-1]
        r1 = pct_change(s, 1)
        r5 = pct_change(s, 5)
        r20 = pct_change(s, 20)
        t = trend(r20)
        price_str = fmt_price(name, price)
        lines.append(
            f"**{name}**: {price_str} "
            f"(1D {fmt_pct(r1)}, 5D {fmt_pct(r5)}, 20D {fmt_pct(r20)}) "
            f"| Trend(20D): {t}"
        )

    lines.append("")
    lines.append(f"*Charts: macro_{today_str}.pdf*")

    # ── BTC vs Nasdaq ────────────────────────────────────────────────────────
    lines.append("")
    lines.append("## BTC vs Nasdaq (20D)")
    lines.append("")

    btc_s = data.get("BTC")
    nas_s = data.get("Nasdaq")
    btc_ret20 = pct_change(btc_s, 20) if btc_s is not None else None
    nas_ret20 = pct_change(nas_s, 20) if nas_s is not None else None

    lines.append(f"- BTC ret20: {fmt_pct(btc_ret20)}")
    lines.append(f"- Nasdaq ret20: {fmt_pct(nas_ret20)}")

    if btc_ret20 is not None and nas_ret20 is not None:
        diff = btc_ret20 - nas_ret20
        lines.append(f"- BTC - Nasdaq (20D): {fmt_pct(diff)}（强弱差）")
    else:
        lines.append("- BTC - Nasdaq (20D): N/A")

    # ── 信号提示 ─────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("## 信号提示（不做结论，仅倾向性提示）")
    lines.append("")

    tnx_s = data.get("10Y Yield (TNX)")
    tnx_r20 = pct_change(tnx_s, 20) if tnx_s is not None else None
    if tnx_r20 is not None:
        direction = "↑" if tnx_r20 > 0 else "↓"
        lines.append(
            f"- Real rates {direction} ({fmt_pct(tnx_r20)} 20D)：通常对黄金偏{'压制' if tnx_r20 > 0 else '支撑'}"
        )

    dxy_s = data.get("DXY")
    dxy_r20 = pct_change(dxy_s, 20) if dxy_s is not None else None
    if dxy_r20 is not None:
        direction = "↑" if dxy_r20 > 0 else "↓"
        lines.append(
            f"- DXY {direction} ({fmt_pct(dxy_r20)} 20D)：通常对风险资产偏{'压制' if dxy_r20 > 0 else '支撑'}"
        )

    vix_s = data.get("VIX")
    vix_r20 = pct_change(vix_s, 20) if vix_s is not None else None
    if vix_r20 is not None:
        direction = "↑" if vix_r20 > 0 else "↓"
        lines.append(
            f"- VIX {direction} ({fmt_pct(vix_r20)} 20D)：风险偏好{'下降' if vix_r20 > 0 else '上升'}"
        )

    if btc_ret20 is not None and nas_ret20 is not None:
        diff = btc_ret20 - nas_ret20
        direction = "走强" if diff > 0 else "走弱"
        lines.append(
            f"- BTC 相对 Nasdaq 20D {direction}（差值 {fmt_pct(diff)}）"
        )

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {today_str} | Data: yfinance | Lean Week 1*")

    return "\n".join(lines)


def main():
    today_str = date.today().isoformat()

    print(f"Fetching data for {today_str}...")
    data = {}
    for name, ticker in TICKERS.items():
        print(f"  {name} ({ticker})...", end=" ", flush=True)
        s = fetch_series(ticker)
        data[name] = s
        print("ok" if s is not None else "FAILED")

    report = build_report(today_str, data)

    print()
    print(report)

    os.makedirs("reports", exist_ok=True)
    out_path = os.path.join("reports", f"macro_{today_str}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved to {out_path}")

    pdf_path = os.path.join("reports", f"macro_{today_str}.pdf")
    save_charts(today_str, data, pdf_path)
    print(f"Charts saved to {pdf_path}")


if __name__ == "__main__":
    main()
