%% plot_all_P4
% Run all three P4 plotting scripts (loads the .mat files, rebuilds the
% figures, and saves .fig + .png next to this file).
here = fileparts(mfilename('fullpath'));
run(fullfile(here, 'plot_P4_01_observability.m'));
run(fullfile(here, 'plot_P4_02_independent_perturbations.m'));
run(fullfile(here, 'plot_P4_03_delta_ratio.m'));
disp('All P4 MATLAB figures saved.');
