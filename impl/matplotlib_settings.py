import matplotlib as m
import matplotlib.ticker
import os

#m.rcParams['axes.unicode_minus'] = False
m.rcParams['text.usetex'] = True
m.rcParams['text.latex.preamble'] = '\input{' + os.getcwd() + '/../text/common-style.tex}'

m.rcParams['font.size'] = 11
m.rcParams['font.family'] = 'serif'
m.rcParams['legend.fontsize'] = 11
m.rcParams['axes.labelsize'] = 11
m.rcParams['axes.labelsize'] = 11
m.rcParams['axes.titlesize'] = 11

m.rcParams['svg.fonttype'] = 'none'
m.rcParams['savefig.dpi'] = 600

m.rcParams["figure.figsize"] = '6.5, 4'
m.rcParams['figure.subplot.left'] = 0.145
m.rcParams['figure.subplot.right'] = 0.855
m.rcParams['figure.subplot.top'] = 1
m.rcParams['figure.subplot.bottom'] = 0.10
m.rcParams['figure.subplot.hspace'] = 0.3

m.rcParams['axes.grid'] = True

margins = 0.02

def ticker_format_func(x, pos):
    if x == int(x):
        x = int(x)
    return r'\num{' + str(x) + '}'

ticker_format = matplotlib.ticker.FuncFormatter(ticker_format_func)


def common_plot_settings(plot, min_x = None, max_x = None, min_y = None, max_y = None, set_limits=True):
    """Common settings for all plots in my thesis.
    Should be applied after all drawing is done."""

    legend = plot.legend()
    if legend is not None:
        legend.get_frame().set_alpha(0.75)

    plot.xaxis.set_major_formatter(ticker_format)
    plot.yaxis.set_major_formatter(ticker_format)

    if set_limits:
        margin = (max_x - min_x) * margins
        plot.set_xlim([min_x - margin, max_x + margin])

        margin = (max_y - min_y) * margins
        plot.set_ylim([min_y - margin, max_y + margin])

