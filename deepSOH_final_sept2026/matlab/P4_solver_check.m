%% P4_solver_check
% Solver check for one cell: V(H) of Figure 7 computed from RK23 runs and from DOP853
% runs. Left: V(H) from DOP853. Right: V_RK23(H) / V_DOP853(H); 1 means the solver
% does not matter. Needs ../data/P4_observability_<cell>_dop853.mat
% (python sim/sim_observability.py --cell <cell> --solver dop853).

P4_settings
fileRK = fullfile(dataDir, ['P4_observability_' solverCheckCell '.mat']);
fileDOP = fullfile(dataDir, ['P4_observability_' solverCheckCell '_dop853.mat']);
if ~isfile(fileDOP)
    fprintf('Solver check skipped: %s not found.\n', fileDOP);
    return
end

[psiRK, cycRK, yRK] = observability_sensitivities(fileRK, capacityCut);
[psiDOP, cycDOP, yDOP] = observability_sensitivities(fileDOP, capacityCut);
K = min(numel(cycRK), numel(cycDOP));        % compare over the cycles both runs share
psiRK = psiRK(1:K, :, :) ./ yRK(1, :);
psiDOP = psiDOP(1:K, :, :) ./ yDOP(1, :);
horizon = cycRK(2:K);

f = figure('Color', 'w', 'Position', [60 60 1350 560], 'Visible', 'off');
ax1 = subplot(1, 2, 1); hold(ax1, 'on'); grid(ax1, 'on'); set(ax1, 'YScale', 'log');
ax2 = subplot(1, 2, 2); hold(ax2, 'on'); grid(ax2, 'on'); set(ax2, 'YScale', 'log');
for j = plotSets
    ch = setChannels{j};
    vRK = prediction_variance(psiRK, ch, ones(1, numel(ch)), [iCap iRes]);
    vDOP = prediction_variance(psiDOP, ch, ones(1, numel(ch)), [iCap iRes]);
    ok = isfinite(vDOP) & vDOP > 0;
    plot(ax1, horizon(ok), vDOP(ok), 'Color', setColors(j, :), 'LineStyle', setStyles{j}, 'LineWidth', 1.5);
    ok = ok & isfinite(vRK) & vRK > 0;
    plot(ax2, horizon(ok), vRK(ok) ./ vDOP(ok), 'Color', setColors(j, :), 'LineStyle', setStyles{j}, 'LineWidth', 1.3);
end
yline(ax2, 1, 'k-', 'LineWidth', 0.8);
xlabel(ax1, 'Diagnostic horizon H [cycles]'); ylabel(ax1, 'Average prediction variance (DOP853)');
xlabel(ax2, 'Diagnostic horizon H [cycles]'); ylabel(ax2, 'V_{RK23}(H) / V_{DOP853}(H)');
legend(ax1, setNames(plotSets), 'Location', 'northeast', 'Box', 'off', 'FontSize', 8);
save_figure(f, figDir, 'P4_solver_check');
