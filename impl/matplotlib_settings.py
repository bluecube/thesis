import matplotlib as m

# We will be saving all plots as svg and rendering texts using
# inkscape's pdf_tex export

m.rcParams['axes.unicode_minus'] = False
m.rcParams['text.usetex'] = False
m.rcParams['font.size'] = 12
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

m.rcParams['axes.grid'] = True
