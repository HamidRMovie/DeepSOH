%% plot_P4_01_observability
% Recreate the P4 observability figures from P4_01_observability.mat.
% The 11-trajectory panel is one figure; the three metric panels are each
% saved as their own figure. No titles. Each figure saved as .fig and .png.

here = fileparts(mfilename('fullpath'));
S = load(fullfile(here, 'P4_01_observability.mat'));

labels    = cellstr(S.labels);
outCols   = cellstr(S.output_columns);
stateCols = cellstr(S.state_columns);
cols      = [outCols(:); stateCols(:)];
panelLabels = {'Capacity [Ah]', 'Resistance [Ohm]', 'Expansion [um]', ...
    'n_{Li} [mol]', 'C_p [Ah]', 'C_n [Ah]', ...
    '\delta_{SEI} [m]', '\delta_{plating} [m]'};

%% Figure: 11 trajectories (3x3), no titles
f1 = figure('Color', 'w', 'Position', [80 80 1400 1000]);
for p = 1:numel(cols)
    ax = subplot(3, 3, p); hold(ax, 'on'); grid(ax, 'on');
    M = S.(cols{p});
    for j = 1:numel(labels)
        plot(ax, S.cycle, M(:, j), 'Color', S.traj_colors(j, :), ...
            'LineStyle', S.traj_linestyles{j}, 'LineWidth', 1.2);
    end
    ylabel(ax, panelLabels{p});
    xlabel(ax, 'Second-life cycle');
end
axL = subplot(3, 3, 9); axis(axL, 'off'); hold(axL, 'on');
h = gobjects(numel(labels), 1);
for j = 1:numel(labels)
    h(j) = plot(axL, NaN, NaN, 'Color', S.traj_colors(j, :), ...
        'LineStyle', S.traj_linestyles{j}, 'LineWidth', 1.6);
end
legend(axL, h, strrep(labels, '_', '\_'), 'Location', 'west', 'Box', 'off', 'FontSize', 8);
base = fullfile(here, 'P4_01_observability_trajectories');
savefig(f1, [base '.fig']);
exportgraphics(f1, [base '.png'], 'Resolution', 150);

%% Metric curves
meas    = cellstr(S.meas_sets);
mMetric = cellstr(S.m_metric);
mSet    = cellstr(S.m_set);

%% Figure: sigma_min(W), Capacity + Resistance only (own figure, no title)
f2 = figure('Color', 'w', 'Position', [80 80 760 560]);
ax = axes('Parent', f2); hold(ax, 'on'); grid(ax, 'on'); set(ax, 'YScale', 'log');
ci  = find(strcmp(meas, 'Capacity + Resistance'), 1);
sel = strcmp(mMetric, 'sigma_min_W') & strcmp(mSet, 'Capacity + Resistance');
xc = S.m_cycle(sel); yv = S.m_value(sel);
% Cycle 1 gives W fewer independent rows than states, so it cannot be full rank;
% the point it plots is the SVD noise floor and it drags the axis down eight decades.
ok = isfinite(yv) & yv > 0 & xc >= 2;
plot(ax, xc(ok), yv(ok), 'Color', S.meas_colors(ci, :), ...
    'LineStyle', S.meas_linestyles{ci}, 'LineWidth', 1.9);
xlabel(ax, 'Last cycle included in W');
ylabel(ax, '\sigma_{min}(W): Capacity + Resistance (higher is better)');
base = fullfile(here, 'P4_01_observability_sigma_min');
savefig(f2, [base '.fig']);
exportgraphics(f2, [base '.png'], 'Resolution', 150);

%% Figures: I-optimality N10 and remaining (each its own figure, no title)
specs = {'Ioptimality_N10',       'P4_01_observability_ioptimality_N10'; ...
         'Ioptimality_remaining', 'P4_01_observability_ioptimality_remaining'};
ioptSets = cellstr(S.iopt_sets);   % sets shown in the prediction-variance figure
for k = 1:size(specs, 1)
    f = figure('Color', 'w', 'Position', [80 80 820 580]);
    ax = axes('Parent', f); hold(ax, 'on'); grid(ax, 'on'); set(ax, 'YScale', 'log');
    for mi = 1:numel(ioptSets)
        sel = strcmp(mMetric, specs{k, 1}) & strcmp(mSet, ioptSets{mi});
        xc = S.m_cycle(sel); yv = S.m_value(sel); ok = isfinite(yv) & yv > 0;
        plot(ax, xc(ok), yv(ok), 'Color', S.iopt_colors(mi, :), ...
            'LineStyle', S.iopt_linestyles{mi}, 'LineWidth', 1.6);
    end
    xlabel(ax, 'Diagnostic horizon H [cycles]');
    ylabel(ax, 'Average prediction variance');
    legend(ax, ioptSets, 'Location', 'northeast', 'Box', 'off', 'FontSize', 8);
    base = fullfile(here, specs{k, 2});
    savefig(f, [base '.fig']);
    exportgraphics(f, [base '.png'], 'Resolution', 150);
end

disp('Saved P4_01 observability figures (trajectories + 3 metric figures)');
