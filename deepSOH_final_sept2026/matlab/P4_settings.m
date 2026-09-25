%% P4_settings
% Settings shared by every P4 figure script (each script starts by running this file).
% Change values here; the simulation data in ../data is not touched.

matlabDir = fileparts(mfilename('fullpath'));
dataDir   = fullfile(matlabDir, '..', 'data');
figDir    = fullfile(matlabDir, '..', 'figures');
if ~exist(figDir, 'dir'), mkdir(figDir); end

% End of second life: each trajectory keeps its last sample before the capacity first
% drops below this value (end_of_life_index.m).
capacityCut = 3.0;                      % [Ah]

% Last cycle of the record in Figures 6 and 7 (the window of the paper's figures).
% [] = the nominal cell's end of life (cycle 125). V(H) averages over all remaining
% cycles, so this changes every point of Figure 7.
observabilityLastCycle = 120;

%% Output channels of the observability runs, in the column order of Psi
channelNames = {'Capacity', 'Resistance', 'Expansion', 'n_Li', 'C_p', 'C_n'};
iCap = 1; iRes = 2; iExp = 3; iNLi = 4; iCp = 5; iCn = 6;

%% Measurement sets: the channels recorded once per cycle
setNames = {'Capacity', 'Resistance', 'Capacity + Resistance', 'Expansion', ...
    'Resistance + Expansion', 'Capacity + Resistance + Expansion', 'eSOH', ...
    'eSOH + Resistance', 'eSOH + Resistance + Expansion'};
setChannels = {iCap, iRes, [iCap iRes], iExp, [iRes iExp], [iCap iRes iExp], ...
    [iNLi iCp iCn], [iNLi iCp iCn iRes], [iNLi iCp iCn iRes iExp]};
setColors = [0 0.447 0.698; 0.8353 0.3686 0; 0 0.6196 0.4510; 0.8 0.4745 0.6549; ...
    0.902 0.6235 0; 0 0 0; 0.5804 0.4039 0.7412; 0.549 0.3373 0.2941; 0 0 0];
setStyles = {'-', '--', '-.', ':', '--', '-.', '-', '--', '-.'};
% The seven sets shown in Figure 7 and in the bounds figure, in legend order.
% All nine are computed; Expansion and Capacity + Resistance + Expansion are not plotted.
plotSets = [1 2 7 3 5 8 9];

%% Measurement uncertainty, used only for the bounds figure
% Uncertainty of ONE measurement of each channel. What sets a bound is the uncertainty of
% the channels that are recorded, not of the output being predicted.
sigma3 = zeros(1, 6);                   % 3-sigma values
sigma3(iCap) = 0.1;                     % [Ah]
sigma3(iRes) = 2e-3;                    % [Ohm], i.e. 2 mOhm
sigma3(iExp) = 10;                      % [um], in-vehicle sensor; 5 optimistic, 20 pessimistic
                                        %       (P4_expansion_uncertainty_notes.md)
sigma3(iNLi) = 0.1 * 3600 / 96485.33;   % [mol], the lithium in 0.1 Ah (3.73 mmol)
sigma3(iCp)  = 0.022;                   % [Ah], ~10% of the average second-life range of C_p
sigma3(iCn)  = 0.052;                   % [Ah], ~10% of the average second-life range of C_n
quotedAt = 3;                           % the values above are 3-sigma values
bandZ    = 3;                           % bounds are drawn at +/- 3 sigma
boundsSummaryCycle = 52;                % cycle at which the bound half-widths are printed
                                        % (the mid-life C/20 test cycle of Figure 3)

%% Solver check (P4_solver_check.m)
% The cell whose DOP853 runs are compared with RK23; must match the DOP853 run in sim/run_all.py.
solverCheckCell = 'high_SEI_low_plating';

%% The three matched cells (Figure 3 and the bounds), fastest-dying first
cellNames  = {'low_SEI_high_plating', 'moderate_SEI_moderate_plating', 'high_SEI_low_plating'};
cellColors = [0.4 0.4 0.4; 0.902 0.6235 0; 0 0.447 0.698];

%% One-at-a-time perturbations (Figure 5)
caseNames  = {'nominal', 'nLi_x0p95', 'Cp_x0p85', 'Cn_x0p90', 'plating_x1p5', 'SEI_x2'};
caseLabels = {'Nominal', 'n_{Li} \times 0.95', 'C_p \times 0.85', 'C_n \times 0.9', ...
    '\delta_{plating} \times 1.5', '\delta_{SEI} \times 2'};
caseColors = [0 0.447 0.698; 0 0 0; 0.8353 0.3686 0; 0 0.6196 0.4510; ...
    0.5333 0.1333 0.3333; 0.902 0.6235 0];
caseStyles = {'-', '--', '--', ':', '--', '-.'};
