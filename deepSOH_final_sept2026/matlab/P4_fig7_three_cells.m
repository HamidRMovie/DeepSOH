%% P4_fig7_three_cells
% Figure 7 for each of the three matched cells: the average prediction variance V(H)
% of the future capacity and resistance, for the measurement sets of P4_settings.
% Each cell's record runs to its own end of life.
% Data: ../data/P4_observability_<cell>.mat, and P4_three_cells.mat for the labels.

P4_settings
load(fullfile(dataDir, 'P4_three_cells.mat'), 'cell_names', 'alpha_SEI');
if ~isequal(cell_names, cellNames)
    error('Cell order in P4_three_cells.mat differs from P4_settings.');
end

f = figure('Color', 'w', 'Position', [40 80 1650 520], 'Visible', 'off');
for c = 1:numel(cellNames)
    [psi, cycle, yNominal] = observability_sensitivities( ...
        fullfile(dataDir, ['P4_observability_' cellNames{c} '.mat']), capacityCut);
    psiNorm = psi ./ yNominal(1, :);          % normalized by the cell's cycle-0 outputs
    horizon = cycle(2:end);

    ax = subplot(1, numel(cellNames), c); hold(ax, 'on'); grid(ax, 'on'); set(ax, 'YScale', 'log');
    for j = plotSets
        ch = setChannels{j};
        V = prediction_variance(psiNorm, ch, ones(1, numel(ch)), [iCap iRes]);
        ok = isfinite(V) & V > 0;
        plot(ax, horizon(ok), V(ok), 'Color', setColors(j, :), 'LineStyle', setStyles{j}, 'LineWidth', 1.5);
    end
    xlim(ax, [0 horizon(end)]);
    title(ax, sprintf('%.0f%% \\delta_{SEI} / %.0f%% \\delta_{plating}', ...
        100 * alpha_SEI(c), 100 * (1 - alpha_SEI(c))));
    xlabel(ax, 'Diagnostic horizon H [cycles]');
    if c == 1
        ylabel(ax, 'Average prediction variance');
        legend(ax, setNames(plotSets), 'Location', 'southwest', 'Box', 'off', 'FontSize', 7);
    end
end
save_figure(f, figDir, 'P4_three_cells_prediction_variance');
