%% P4_fig3_three_cells
% Figure 3: three cells with the same capacity and resistance at the end of first use
% (EOFU) but a different SEI/plating split. Left: capacity, resistance and irreversible
% expansion over the second life. Right: C/20 voltage at three cycles, the same for all
% cells (start, mid-life and end of life of the fastest-dying cell).
% Data: ../data/P4_three_cells.mat

P4_settings
load(fullfile(dataDir, 'P4_three_cells.mat'), 'cell_names', 'alpha_SEI', 'second_life', 'rpt');
if ~isequal(cell_names, cellNames)
    error('Cell order in P4_three_cells.mat differs from P4_settings.');
end
nCells = numel(cellNames);
cellLabels = cell(1, nCells);
for c = 1:nCells
    cellLabels{c} = sprintf('%.0f%% \\delta_{SEI} / %.0f%% \\delta_{plating}', ...
        100 * alpha_SEI(c), 100 * (1 - alpha_SEI(c)));
end

% each cell ends at its own end of life
lastRow = zeros(1, nCells);
for c = 1:nCells
    lastRow(c) = end_of_life_index(second_life.capacity_Ah(:, c), capacityCut);
end

f = figure('Color', 'w', 'Position', [50 50 1350 1000], 'Visible', 'off');

%% Left column: capacity, resistance, expansion
lifeData   = {second_life.capacity_Ah, second_life.resistance_Ohm, second_life.expansion_um};
lifeLabels = {'Capacity [Ah]', 'Resistance [Ohm]', 'Irreversible expansion [um]'};
lifeTags   = {'(a)', '(b)', '(c)'};
for p = 1:3
    ax = subplot(3, 2, 2 * p - 1); hold(ax, 'on'); grid(ax, 'on');
    y = lifeData{p};
    for c = 1:nCells
        k = lastRow(c);
        plot(ax, second_life.cycle(1:k), y(1:k, c), 'Color', cellColors(c, :), 'LineWidth', 1.9);
    end
    ylabel(ax, lifeLabels{p});
    text(ax, 0.01, 1.07, lifeTags{p}, 'Units', 'normalized', 'FontWeight', 'bold', 'FontSize', 11);

    if p <= 2
        % capacity and resistance: all three cells start from the same point
        plot(ax, 0, y(1, 1), 'ko', 'MarkerSize', 9, 'LineWidth', 1.6, 'HandleVisibility', 'off');
        xr = xlim(ax);
        text(ax, 0.055 * (xr(2) - xr(1)), y(1, 1), 'Same EOFU performance', ...
            'FontSize', 8, 'FontWeight', 'bold', 'VerticalAlignment', 'middle', ...
            'BackgroundColor', 'w', 'Margin', 1);
    else
        % expansion differs already at EOFU (log scale: the cells span ~50 to ~1500 um)
        set(ax, 'YScale', 'log');
        for c = 1:nCells
            plot(ax, 0, y(1, c), 'o', 'MarkerSize', 7, 'LineWidth', 1.4, ...
                'MarkerEdgeColor', cellColors(c, :), 'HandleVisibility', 'off');
        end
        xr = xlim(ax);
        text(ax, 0.055 * (xr(2) - xr(1)), 1.12 * max(y(1, :)), 'Different EOFU expansion', ...
            'FontSize', 8, 'FontWeight', 'bold', 'VerticalAlignment', 'middle', ...
            'BackgroundColor', 'w', 'Margin', 1);
    end

    % cycles of the mid-life and end-of-life C/20 tests
    xline(ax, rpt.cycles(2), '--', 'Color', [0.45 0.45 0.45], 'LineWidth', 0.9, 'HandleVisibility', 'off');
    xline(ax, rpt.cycles(3), '--', 'Color', [0.45 0.45 0.45], 'LineWidth', 0.9, 'HandleVisibility', 'off');
    if p == 1
        legend(ax, cellLabels, 'Location', 'northeast', 'Box', 'off', 'FontSize', 8);
    end
end
xlabel(ax, 'Cycle number in second life');

%% Right column: C/20 voltage at the three test cycles
rptTags = {'(d)', '(e)', '(f)'};
for s = 1:3
    ax = subplot(3, 2, 2 * s); hold(ax, 'on'); grid(ax, 'on');
    for c = 1:nCells
        n = rpt.n_samples(s, c);
        plot(ax, rpt.time_h(1:n, s, c), rpt.voltage_V(1:n, s, c), ...
            'Color', cellColors(c, :), 'LineWidth', 1.6);
    end
    title(ax, sprintf('Cycle %d', rpt.cycles(s)));
    text(ax, 0.01, 1.07, rptTags{s}, 'Units', 'normalized', 'FontWeight', 'bold', 'FontSize', 11);
    ylabel(ax, 'Voltage [V]');
end
xlabel(ax, 'RPT time [h]');

save_figure(f, figDir, 'P4_03_delta_ratio');

fprintf('\nThree cells: end of life at cycle');
fprintf(' %d', second_life.cycle(lastRow)); fprintf('\n');
