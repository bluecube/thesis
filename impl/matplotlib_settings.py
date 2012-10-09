import matplotlib as m

# We will be saving all plots as svg and rendering texts using
# inkscape's pdf_tex export

m.rcParams['axes.unicode_minus'] = False
m.rcParams['text.usetex'] = False
m.rcParams['font.size'] = 11
m.rcParams['legend.fontsize'] = 12
m.rcParams['axes.labelsize'] = 12
m.rcParams['axes.labelsize'] = 12
m.rcParams['axes.titlesize'] = 12
m.rcParams['svg.fonttype'] = 'none'
m.rcParams['savefig.dpi'] = 1800

m.rcParams["figure.figsize"] = '5.5, 4'
m.rcParams['figure.subplot.left'] = 0.08
m.rcParams['figure.subplot.right'] = 0.92
m.rcParams['figure.subplot.top'] = 1
m.rcParams['figure.subplot.bottom'] = 0.10
m.rcParams['figure.subplot.hspace'] = 0.3

m.rcParams['axes.grid'] = True

margins = 0.02

def common_plot_settings(plot, min_x = None, max_x = None, min_y = None, max_y = None, set_limits=True):
    """Common settings for all plots in my thesis.
    Should be applied after all drawing is done."""
    plot.legend().get_frame().set_alpha(0.75)

    if set_limits:
        margin = (max_x - min_x) * margins
        plot.set_xlim([min_x - margin, max_x + margin])

        margin = (max_y - min_y) * margins
        plot.set_ylim([min_y - margin, max_y + margin])

