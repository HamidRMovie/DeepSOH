%% P4_fig5_perturbations
% Figure 5: capacity and resistance over the second life when one deepSOH state is
% changed at the start of second use and the others are kept at their nominal values.
% Data: ../data/P4_perturbations.mat

P4_settings
load(fullfile(dataDir, 'P4_perturbations.mat'), 'case_names', 'second_life');
if ~isequal(case_names, caseNames)
    error('Case order in P4_perturbations.mat differs from P4_settings.');
end

f = figure('Color', 'w', 'Position', [80 80 1050 800], 'Visible', 'off');
panelData   = {second_life.capacity_Ah, second_life.resistance_Ohm};
panelLabels = {'Capacity [Ah]', 'Resistance [Ohm]'};
panelTags   = {'(a)', '(b)'};
ax = gobjects(2, 1);
for p = 1:2
    ax(p) = subplot(2, 1, p); hold(ax(p), 'on'); grid(ax(p), 'on');
    y = panelData{p};
    for i = 1:numel(caseNames)
        k = end_of_life_index(second_life.capacity_Ah(:, i), capacityCut);
        plot(ax(p), second_life.cycle(1:k), y(1:k, i), 'Color', caseColors(i, :), ...
            'LineStyle', caseStyles{i}, 'LineWidth', 1.8);
    end
    ylabel(ax(p), panelLabels{p});
    text(ax(p), 0.015, 0.08, panelTags{p}, 'Units', 'normalized', 'FontSize', 14, 'FontWeight', 'bold');
end
legend(ax(1), caseLabels, 'Location', 'northoutside', 'Orientation', 'horizontal', ...
    'NumColumns', 3, 'Box', 'on');
xlabel(ax(2), 'Cycle number in second life');
linkaxes(ax, 'x');
xlim(ax(2), [0 140]);

save_figure(f, figDir, 'P4_02_independent_perturbations_life');
