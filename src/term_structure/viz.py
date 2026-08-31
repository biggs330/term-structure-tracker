"""Step 3: regime-shaded price chart + animated curve."""

import matplotlib.animation as animation
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

REGIME_COLORS = {"contango": "#c8e6c9", "backwardation": "#ffcdd2"}


def plot_regime_shaded(curve: pd.DataFrame, regime: pd.Series, out_path: str) -> None:
    """CL1 price line with background shading for each regime streak."""
    fig, ax = plt.subplots(figsize=(12, 5))

    streak_id = (regime != regime.shift()).cumsum()
    for _, idx in regime.groupby(streak_id).groups.items():
        r = regime.loc[idx].iloc[0]
        ax.axvspan(idx[0], idx[-1], color=REGIME_COLORS[r], alpha=0.6, linewidth=0)

    ax.plot(curve.index, curve["CL1"], color="black", linewidth=1.2)

    ax.set_title("WTI Front-Month Price with Contango/Backwardation Regimes")
    ax.set_ylabel("Price ($/bbl)")
    ax.set_xlabel("Date")

    handles = [
        mpatches.Patch(color=REGIME_COLORS["contango"], label="Contango"),
        mpatches.Patch(color=REGIME_COLORS["backwardation"], label="Backwardation"),
        plt.Line2D([0], [0], color="black", linewidth=1.2, label="CL1 price"),
    ]
    ax.legend(handles=handles, loc="upper left")

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def animate_curve(curve: pd.DataFrame, out_path: str, stride: int = 5) -> None:
    """Animate the CL1..CL6 curve shape over time, one frame per sampled date.

    stride: only render every Nth day (default 5, ~weekly) so the GIF stays
    a reasonable length instead of one frame per trading day.
    """
    months_out = list(range(1, curve.shape[1] + 1))
    frame_indices = list(range(0, len(curve), stride))
    if frame_indices[-1] != len(curve) - 1:
        frame_indices.append(len(curve) - 1)  # always end on the most recent date

    fig, ax = plt.subplots(figsize=(7, 5))
    line, = ax.plot([], [], marker="o", color="steelblue")
    date_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=12, fontweight="bold")

    ax.set_xlim(0.5, len(months_out) + 0.5)
    ax.set_xticks(months_out)
    ax.set_xticklabels([f"CL{m}" for m in months_out])
    ax.set_xlabel("Contract (months out)")
    ax.set_ylabel("Price ($/bbl)")
    ax.set_title("WTI Futures Curve")

    y_min, y_max = curve.min().min(), curve.max().max()
    pad = (y_max - y_min) * 0.1
    ax.set_ylim(y_min - pad, y_max + pad)

    def update(frame_idx):
        row = curve.iloc[frame_idx]
        line.set_data(months_out, row.values)
        date_text.set_text(str(curve.index[frame_idx].date()))
        return line, date_text

    anim = animation.FuncAnimation(fig, update, frames=frame_indices, interval=120, blit=True)
    anim.save(out_path, writer="pillow", fps=8)
    plt.close(fig)
