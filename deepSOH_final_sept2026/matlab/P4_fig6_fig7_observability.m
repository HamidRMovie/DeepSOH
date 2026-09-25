%% P4_fig6_fig7_observability
% Figure 6: sigma_min of the observability Gramian from capacity and resistance.
% Figure 7: average prediction variance V(H) of the future capacity and resistance, for
%           the measurement sets of P4_settings.
% Data: ../data/P4_observability_nominal.mat (nominal run and the +/- epsilon runs).

P4_settings

[psi, cycle, yNominal] = observability_sensitivities( ...
    fullfile(dataDir, 'P4_observability_nominal.mat'), capacityCut);
if ~isempty(observabilityLastCycle)          % shorter record window, see P4_settings
    keep = cycle <= observabilityLastCycle;
    psi = psi(keep, :, :);
    cycle = cycle(keep);
    yNominal = yNominal(keep, :);
end
K = numel(cycle);

% Normalize every channel by the nominal run's value at cycle 0, so Psi is dimensionless.
y0 = yNominal(1, :);
psiNorm = psi ./ y0;

%% Figure 6: sigma_min(W) over the first k cycles, W from capacity and resistance (eq. 21)
M = [iCap iRes];
W = zeros(5);
sigmaMin = zeros(K, 1);
for k = 1:K
    Pk = reshape(psiNorm(k, M, :), numel(M), 5);
    W = W + Pk' * Pk;
    sigmaMin(k) = min(svd(W));
end

% Before cycle 2 the record has fewer independent rows than states, so W cannot be full
% rank and sigma_min there is SVD round-off; those points are not drawn.
show = cycle >= 2;
f6 = figure('Color', 'w', 'Position', [80 80 760 560], 'Visible', 'off');
semilogy(cycle(show), sigmaMin(show), 'Color', setColors(3, :), ...
    'LineStyle', setStyles{3}, 'LineWidth', 1.9);
grid on
xlim([0 cycle(end)]);
xlabel('Last cycle included in W');
ylabel('\sigma_{min}(W): Capacity + Resistance (higher is better)');
save_figure(f6, figDir, 'P4_01_observability_sigma_min');

%% Figure 7: V(H) for every measurement set (eq. 25)
% Equal relative noise on every channel cancels, so sigma = 1 in normalized units.
V = nan(K - 1, numel(setNames));
for j = 1:numel(setNames)
    ch = setChannels{j};
    V(:, j) = prediction_variance(psiNorm, ch, ones(1, numel(ch)), [iCap iRes]);
end
horizon = cycle(2:end);            % V(H) is reported at the first predicted cycle

f7 = figure('Color', 'w', 'Position', [80 80 820 580], 'Visible', 'off');
ax = axes(f7); hold(ax, 'on'); grid(ax, 'on'); set(ax, 'YScale', 'log');
for j = plotSets
    ok = isfinite(V(:, j)) & V(:, j) > 0;
    plot(ax, horizon(ok), V(ok, j), 'Color', setColors(j, :), ...
        'LineStyle', setStyles{j}, 'LineWidth', 1.6);
end
xlim(ax, [0 horizon(end)]);
xlabel(ax, 'Diagnostic horizon H [cycles]');
ylabel(ax, 'Average prediction variance');
legend(ax, setNames(plotSets), 'Location', 'northeast', 'Box', 'off', 'FontSize', 8);
save_figure(f7, figDir, 'P4_01_observability_ioptimality_remaining');

%% Summary
fprintf('\nNominal cell, %d cycles (last cycle %d)\n', K, cycle(end));
fprintf('sigma_min(W), capacity + resistance, at the last cycle: %.4g\n', sigmaMin(end));
fprintf('V(H) at the last horizon:\n');
for j = 1:numel(setNames)
    fprintf('  %-36s %.4g\n', setNames{j}, V(end, j));
end
