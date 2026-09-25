%% P4_fig_bounds_three_cells
% Bounds on the average prediction error of capacity and resistance for the three
% matched cells. One row per measurement set, capacity on the left, resistance on the
% right. At cycle H each cell's trajectory is wrapped in +/- bandZ standard deviations of
% the average prediction error over its remaining life (cycle H to end of life), given a
% record of cycles 0 to H-1 (eq. 25 with the measurement uncertainties sigma3 of
% P4_settings). This is the horizon convention of Figure 7.
% Data: ../data/P4_observability_<cell>.mat, and P4_three_cells.mat for the labels.

P4_settings
load(fullfile(dataDir, 'P4_three_cells.mat'), 'cell_names', 'alpha_SEI');
if ~isequal(cell_names, cellNames)
    error('Cell order in P4_three_cells.mat differs from P4_settings.');
end
nCells = numel(cellNames);
cellLabels = cell(1, nCells);
for c = 1:nCells
    cellLabels{c} = sprintf('%.0f%% \\delta_{SEI} / %.0f%% \\delta_{plating}', ...
        100 * alpha_SEI(c), 100 * (1 - alpha_SEI(c)));
end

nRows = numel(plotSets);
targets = [iCap iRes];
scale = [1, 1e3];                       % draw capacity in Ah, resistance in mOhm
ylabels = {'Capacity [Ah]', 'Resistance [m\Omega]'};
summary = nan(nRows, 2, nCells);        % bound half-width at boundsSummaryCycle: set x output x cell

f = figure('Color', 'w', 'Position', [40 20 980 1900], 'Visible', 'off');
ax = gobjects(nRows, 2);
for r = 1:nRows
    for t = 1:2
        ax(r, t) = subplot(nRows, 2, 2 * (r - 1) + t);
        hold(ax(r, t), 'on'); grid(ax(r, t), 'on');
    end
end

yMin = [inf inf]; yMax = [-inf -inf]; xMax = 0;
legendLines = gobjects(1, nCells);
for c = 1:nCells
    [psi, cycle, yNominal] = observability_sensitivities( ...
        fullfile(dataDir, ['P4_observability_' cellNames{c} '.mat']), capacityCut);
    xMax = max(xMax, cycle(end));
    for t = 1:2
        yTraj = yNominal(:, targets(t)) * scale(t);
        yMin(t) = min(yMin(t), min(yTraj));
        yMax(t) = max(yMax(t), max(yTraj));
        for r = 1:nRows
            ch = setChannels{plotSets(r)};
            vbar = prediction_variance(psi, ch, sigma3(ch) / quotedAt, targets(t));
            half = bandZ * sqrt(vbar) * scale(t);      % reported at cycles 2..K
            ok = isfinite(half);
            h = cycle([false; ok]);
            yH = yTraj([false; ok]);
            fill(ax(r, t), [h; flipud(h)], [yH - half(ok); flipud(yH + half(ok))], ...
                cellColors(c, :), 'FaceAlpha', 0.20, 'EdgeColor', 'none');
            hLine = plot(ax(r, t), cycle, yTraj, '-', 'Color', cellColors(c, :), 'LineWidth', 1.3);
            if r == 1 && t == 2
                legendLines(c) = hLine;
            end
            k = find(cycle(2:end) == boundsSummaryCycle, 1);
            if ~isempty(k)
                summary(r, t, c) = half(k);
            end
        end
    end
end

for r = 1:nRows
    for t = 1:2
        pad = 0.08 * (yMax(t) - yMin(t));
        ylim(ax(r, t), [yMin(t) - pad, yMax(t) + pad]);
        xlim(ax(r, t), [0 xMax]);
        set(ax(r, t), 'FontSize', 8);
        ylabel(ax(r, t), ylabels{t}, 'FontSize', 8.5);
        if r < nRows
            set(ax(r, t), 'XTickLabel', []);
        else
            xlabel(ax(r, t), 'Second-life cycle (bound: from this cycle to end of life)', 'FontSize', 8.5);
        end
    end
    text(ax(r, 1), 0.03, 0.14, setNames{plotSets(r)}, 'Units', 'normalized', ...
        'FontSize', 9, 'FontWeight', 'bold', 'VerticalAlignment', 'bottom');
end
legend(ax(1, 2), legendLines, cellLabels, 'Location', 'northwest', 'Box', 'off', 'FontSize', 7.5);

save_figure(f, figDir, 'P4_three_cell_bounds');

%% Summary: bound half-width at H = boundsSummaryCycle
fprintf('\n+/-%g sigma bound half-width at H = %d  (capacity [Ah] / resistance [mOhm])\n', bandZ, boundsSummaryCycle);
for r = 1:nRows
    fprintf('%-32s', setNames{plotSets(r)});
    for c = 1:nCells
        fprintf('  %8.3f /%8.2f', summary(r, 1, c), summary(r, 2, c));
    end
    fprintf('\n');
end
