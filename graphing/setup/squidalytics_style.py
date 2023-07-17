import matplotlib.pyplot as plt
import seaborn as sns


def setup_style() -> None:
    sns.set(style="darkgrid", context="talk")
    sns.color_palette("bright")
    plt.rcParams["axes.facecolor"] = "black"
    plt.rcParams["figure.facecolor"] = "black"

    plt.rcParams["grid.color"] = "gray"
    plt.rcParams["grid.linestyle"] = ":"
    plt.rcParams["grid.linewidth"] = 0.5

    plt.rcParams["axes.edgecolor"] = "white"
    plt.rcParams["axes.labelcolor"] = "white"
    plt.rcParams["axes.titlecolor"] = "white"

    plt.rcParams["xtick.color"] = "white"
    plt.rcParams["ytick.color"] = "white"

    plt.rcParams["text.color"] = "white"


class COLORS:
    accent_color = "#ad5ad7"
    accent_darker = "#7a28a3"
