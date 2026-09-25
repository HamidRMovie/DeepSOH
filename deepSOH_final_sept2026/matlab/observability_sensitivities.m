function [psi, cycle, yNominal] = observability_sensitivities(matFile, capacityCut)
%OBSERVABILITY_SENSITIVITIES  Psi of eq. (20) from one observability data file.
%   The file holds the nominal run and, for each of the five deepSOH states, one run
%   started with that state raised by epsilon and one with it lowered by epsilon
%   (relative change). Psi is the central difference of every output channel between
%   the two, per unit relative change of the state.
%
%   psi       K x 6 x 5  (cycle, channel, state), channels in the order of P4_settings
%   cycle     K x 1      second-life cycle of each row
%   yNominal  K x 6      the nominal run's outputs
%   All rows are cut at the nominal run's end of life (end_of_life_index.m).

d = load(matFile);                 % second_life, run_names, epsilon, ...
s = d.second_life;
K = end_of_life_index(s.capacity_Ah(:, 1), capacityCut);

% outputs: K cycles x runs x 6 channels
Y = cat(3, s.capacity_Ah(1:K, :), s.resistance_Ohm(1:K, :), s.expansion_um(1:K, :), ...
    s.nLi_mol(1:K, :), s.Cp_Ah(1:K, :), s.Cn_Ah(1:K, :));
if any(isnan(Y(:)))
    error('A perturbed run in %s ends before the nominal end of life.', matFile);
end

states = {'nLi', 'Cp', 'Cn', 'delta_SEI', 'delta_pl'};
psi = zeros(K, 6, 5);
for i = 1:5
    plus  = strcmp(d.run_names, [states{i} '_plus']);
    minus = strcmp(d.run_names, [states{i} '_minus']);
    if nnz(plus) ~= 1 || nnz(minus) ~= 1
        error('%s needs exactly one %s_plus and one %s_minus run.', matFile, states{i}, states{i});
    end
    psi(:, :, i) = reshape(Y(:, plus, :) - Y(:, minus, :), K, 6) / (2 * d.epsilon);
end
cycle = s.cycle(1:K);
yNominal = reshape(Y(:, strcmp(d.run_names, 'nominal'), :), K, 6);
end
