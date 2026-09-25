function save_figure(f, figDir, name)
%SAVE_FIGURE  Save figure f as <name>.fig and <name>.png (150 dpi) in figDir, then close it.
%   The figures are drawn off screen; the .fig is set to open visible in MATLAB.
set(f, 'CreateFcn', 'set(gcbo, ''Visible'', ''on'')');
savefig(f, fullfile(figDir, [name '.fig']));
exportgraphics(f, fullfile(figDir, [name '.png']), 'Resolution', 150);
close(f);
end
