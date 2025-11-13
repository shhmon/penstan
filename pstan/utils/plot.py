import matplotlib.pyplot as plt

def scatter_dot(df, ax, column, y, color=None, label=None, marker='o', s=12, **kwargs):
    """Plot signal indicators as scatter points"""
    if column not in df.columns:
        return
    signal_positions = df.index[df[column].astype(bool)]
    if len(signal_positions) == 0:
        return
    signal_positions = [df.index.get_loc(dt) for dt in signal_positions]
    ax.scatter(signal_positions, y, 
               color=color, s=s, zorder=6, label=label or column, marker=marker, linewidths=1, **kwargs)

THEME = {
    'bg': '#0E1117',
    'plot_bg': '#1C1F26',
    'text': '#ECEFF4',
    'grid': '#2E3440',
    'bullish': '#00C853',
    'bearish': '#FF5252',
    'neutral': '#607D8B',
    'neutral_light': '#78909C',
    'volume': '#1E88E5',
    'accent_amber': '#FFC107',
    'accent_purple': '#9C27B0',
    'accent_cyan': '#00BCD4',
    'white': '#FFFFFF',
    'zero_line': '#ECEFF4',
}

def dark_theme_plt():
    plt.style.use("dark_background")
    plt.rcParams.update({
        # Background colors
        'figure.facecolor': THEME['bg'],
        'axes.facecolor': THEME['bg'],
        
        # Text colors
        'text.color': THEME['text'],
        'axes.labelcolor': THEME['text'],
        'xtick.color': THEME['text'],
        'ytick.color': THEME['text'],
        
        # Grid
        'grid.color': '#2E3440',
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'axes.grid': True,
        
        # Spines (borders)
        'axes.edgecolor': THEME['text'],
        'axes.linewidth': 1.2,
        
        # Font sizes
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
    })
