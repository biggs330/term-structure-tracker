from . import data, metrics, viz
from .config import OUTPUTS


def main() -> None:
    curve = data.pull_curve()
    slope = metrics.slope(curve)
    regime = metrics.regime_label(slope)
    label = metrics.one_line_label(regime, slope)

    chart_path = OUTPUTS / "regime_chart.png"
    animation_path = OUTPUTS / "curve_animation.gif"
    label_path = OUTPUTS / "label.txt"

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    viz.plot_regime_shaded(curve, regime, str(chart_path))
    viz.animate_curve(curve, str(animation_path))
    label_path.write_text(label + "\n")

    print(label)
    print(f"Saved: {chart_path}")
    print(f"Saved: {animation_path}")
    print(f"Saved: {label_path}")


if __name__ == "__main__":
    main()
