%% P4_plot_all
% Build every P4 figure from the .mat files in ../data. Figures go to ../figures.
% The four paper figures keep the file names used in the manuscript.

P4_fig3_three_cells              % Figure 3
P4_fig5_perturbations            % Figure 5
P4_fig6_fig7_observability       % Figures 6 and 7
P4_fig7_three_cells              % Figure 7 for each of the three cells
P4_fig_bounds_three_cells        % bounds on the prediction error, three cells
P4_solver_check                  % RK23 vs DOP853 (skipped if the DOP853 data is missing)
disp('All P4 figures saved.');
