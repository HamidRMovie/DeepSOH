%% plot_P4_02_independent_perturbations
% Recreate the P4 independent-perturbation second-life figures from
% P4_02_independent_perturbations.mat. No titles. Saved as .fig + .png.
%
% Aug 25 revisions (author feedback):
%  - Nominal trajectory is now BLUE solid (matches manuscript text);
%    n_Li x 0.95 takes black dashed.
%  - Life figure: every trajectory truncated at a COMMON retained
%    capacity CAP_CUT so all cases end at the same absolute capacity.
%  - Panels carry (a) and (b) labels.
% Sep 1 revision (author request): CAP_CUT lowered from 3.6 to 3.0 Ah.
%    The six plotted cases were re-simulated to the 60% termination by
%    sim/regenerate_perturbations_to_3Ah.py so all reach the new cut.

here = fileparts(mfilename('fullpath'));
S = load(fullfile(here, 'P4_02_independent_perturbations.mat'));

CAP_CUT = 3.0;   % [Ah] common end-of-window capacity for the life figure

cases = cellstr(S.cases);
labMap = containers.Map( ...
    {'nominal', 'nLi_x0p95', 'Cp_x0p85', 'Cn_x0p90', 'plating_x1p5', 'SEI_x2'}, ...
    {'Nominal', 'n_{Li} \times 0.95', 'C_p \times 0.85', 'C_n \times 0.9', ...
     '\delta_{plating} \times 1.5', '\delta_{SEI} \times 2'});
dispLabels = cell(size(cases));
for i = 1:numel(cases)
    if isKey(labMap, cases{i})
        dispLabels{i} = labMap(cases{i});
    else
        dispLabels{i} = strrep(cases{i}, '_', '\_');
    end
end

% Colour override: nominal <- blue (Wong #0072B2), nLi <- black.
colors = S.colors;
iNom = find(strcmp(cases, 'nominal'));
iNli = find(strcmp(cases, 'nLi_x0p95'));
colors(iNom, :) = [0 0.447 0.698];
colors(iNli, :) = [0 0 0];

%% Figure 1: capacity and resistance (second life only, common capacity cut)
f1 = figure('Color', 'w', 'Position', [80 80 1050 800], 'Visible', 'off');
panels = {'capacity_Ah', 'Capacity [Ah]'; 'resistance_Ohm', 'Resistance [Ohm]'};
panelTag = {'(a)', '(b)'};
axs = gobjects(2, 1);
for p = 1:size(panels, 1)
    ax = subplot(2, 1, p); hold(ax, 'on'); grid(ax, 'on');
    axs(p) = ax;
    for i = 1:numel(cases)
        d = S.(cases{i});
        cap = d.capacity_Ah;
        k = find(cap <= CAP_CUT, 1, 'first');   % first sample at/below cut
        if isempty(k), k = numel(cap); end
        plot(ax, d.cycle(1:k), d.(panels{p, 1})(1:k), 'Color', colors(i, :), ...
            'LineStyle', S.linestyles{i}, 'LineWidth', 1.8);
    end
    ylabel(ax, panels{p, 2});
    text(ax, 0.015, 0.08, panelTag{p}, 'Units', 'normalized', ...
        'FontSize', 14, 'FontWeight', 'bold');
    if p == 1
        legend(ax, dispLabels, 'Location', 'northoutside', ...
            'Orientation', 'horizontal', 'NumColumns', 3, 'Box', 'on');
    end
end
xlabel(axs(2), 'Cycle number in second life');
linkaxes(axs, 'x');
xlim(axs(2), [0 140]);
base = fullfile(here, 'P4_02_independent_perturbations_life');
savefig(f1, [base '.fig']);
exportgraphics(f1, [base '.png'], 'Resolution', 150);
close(f1);

%% Figure 2: DeepSOH state trajectories (3x2) -- same colour override
sc = cellstr(S.state_columns);
stateLabels = {'n_{Li} [mol]', 'C_p [Ah]', 'C_n [Ah]', ...
    '\delta_{SEI} [m]', '\delta_{plating} [m]'};
f2 = figure('Color', 'w', 'Position', [80 80 1150 1000], 'Visible', 'off');
for p = 1:numel(sc)
    ax = subplot(3, 2, p); hold(ax, 'on'); grid(ax, 'on');
    for i = 1:numel(cases)
        d = S.(cases{i});
        plot(ax, d.cycle, d.(sc{p}), 'Color', colors(i, :), ...
            'LineStyle', S.linestyles{i}, 'LineWidth', 1.6);
    end
    ylabel(ax, stateLabels{p});
    xlabel(ax, 'Second-life cycle');
end
axL = subplot(3, 2, 6); axis(axL, 'off'); hold(axL, 'on');
h = gobjects(numel(cases), 1);
for i = 1:numel(cases)
    h(i) = plot(axL, NaN, NaN, 'Color', colors(i, :), ...
        'LineStyle', S.linestyles{i}, 'LineWidth', 2);
end
legend(axL, h, dispLabels, 'Location', 'west', 'Box', 'off');
base = fullfile(here, 'P4_02_independent_perturbation_states');
savefig(f2, [base '.fig']);
exportgraphics(f2, [base '.png'], 'Resolution', 150);
close(f2);

disp('Saved P4_02 independent-perturbation figures (blue nominal, (a)/(b), 3.0 Ah cut)');
