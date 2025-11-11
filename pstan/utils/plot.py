
def scatter_dot(df, ax, column, y, color=None, label=None, marker='dot', s=12, **kwargs):
    """Plot signal indicators as scatter points"""
    if column not in df.columns:
        return
    signal_positions = df.index[df[column].astype(bool)]
    if len(signal_positions) == 0:
        return
    signal_positions = [df.index.get_loc(dt) for dt in signal_positions]
    ax.scatter(signal_positions, [y]*len(signal_positions), 
               color=color, s=s, zorder=6, label=label or column, marker=marker, linewidths=2, **kwargs)
