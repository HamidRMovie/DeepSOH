%% plot_P4_03_delta_ratio
% Recreate the P4 matched-resistance delta-ratio results from
% P4_03_delta_ratio.mat as a SINGLE figure combining the second-life
% capacity/resistance/expansion (left column) and the C/20 beginning /
% middle / end reference tests (right column). No titles. Saved as .fig + .png.

here = fileparts(mfilename('fullpath'));
S = load(fullfile(here, 'P4_03_delta_ratio.mat'));

cases = cellstr(S.cases);
labMap = containers.Map( ...
    {'low_SEI_high_plating', 'moderate_SEI_moderate_plating', 'high_SEI_low_plating'}, ...
    {'10% \delta_{SEI} / 90% \delta_{plating}', ...
     '26% \delta_{SEI} / 74% \delta_{plating}', ...
     '90% \delta_{SEI} / 10% \delta_{plating}'});
dispLabels = cell(size(cases));
for i = 1:numel(cases)
    dispLabels{i} = labMap(cases{i});
end

f = figure('Color', 'w', 'Position', [50 50 1350 1000], 'Visible', 'off');

% Left column: capacity / resistance / expansion (second life only)
lifePanels = {'capacity_Ah',   'Capacity [Ah]'; ...
              'resistance_Ohm', 'Resistance [Ohm]'; ...
              'expansion_um',   'Irreversible expansion [um]'};
lifePos = [1 3 5];
for p = 1:size(lifePanels, 1)
    ax = subplot(3, 2, lifePos(p)); hold(ax, 'on'); grid(ax, 'on');
    for i = 1:numel(cases)
        d = S.(cases{i});
        plot(ax, d.cycle, d.(lifePanels{p, 1}), 'Color', S.colors(i, :), 'LineWidth', 1.9);
    end
    ylabel(ax, lifePanels{p, 2});
    % panel letter, above the top-left corner (the caption references (a)-(f))
    leftTags = {'(a)', '(b)', '(c)'};
    text(ax, 0.01, 1.07, leftTags{p}, 'Units', 'normalized', ...
        'FontWeight', 'bold', 'FontSize', 11);
    if strcmp(lifePanels{p, 1}, 'expansion_um')
        % the three cells start within ~30 um of each other; on a linear axis up to
        % ~1500 um they sit on top of one another, so use a log scale
        set(ax, 'YScale', 'log');
    end
    % Mark the common starting point: all three cells are matched in capacity
    % and resistance at the end of first use (EOFU), i.e. second-life cycle 0.
    if p <= 2
        y0 = S.(cases{1}).(lifePanels{p, 1})(1);
        plot(ax, 0, y0, 'ko', 'MarkerSize', 9, 'LineWidth', 1.6, ...
            'MarkerFaceColor', 'none', 'HandleVisibility', 'off');
        xr = xlim(ax);
        % place the label to the RIGHT of the marker, vertically centred on it:
        % avoids clipping at the axis top and overlapping the curves.
        text(ax, 0 + 0.055*(xr(2)-xr(1)), y0, ...
            'Same EOFU performance', 'FontSize', 8, 'FontWeight', 'bold', ...
            'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
            'BackgroundColor', 'w', 'Margin', 1);
    else
        % expansion: the EOFU values DIFFER; mark each cell's own start
        yTop = 0;
        for i = 1:numel(cases)
            yi = S.(cases{i}).expansion_um(1);
            yTop = max(yTop, yi);
            plot(ax, 0, yi, 'o', 'MarkerSize', 7, 'LineWidth', 1.4, ...
                'MarkerEdgeColor', S.colors(i, :), 'MarkerFaceColor', 'none', ...
                'HandleVisibility', 'off');
        end
        xr = xlim(ax);
        text(ax, 0 + 0.055*(xr(2)-xr(1)), yTop*1.12, ...
            'Different EOFU expansion', 'FontSize', 8, 'FontWeight', 'bold', ...
            'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
            'BackgroundColor', 'w', 'Margin', 1);
    end
    % RPT cycles: mid-life and end of life of the fastest-dying cell, i.e. the
    % cycles at which the right-column C/20 tests are taken.
    rptMid = S.(cases{1}).rpt.middle.cycle;
    rptEnd = S.(cases{1}).rpt.ending.cycle;
    xline(ax, rptMid, '--', 'Color', [0.45 0.45 0.45], 'LineWidth', 0.9, ...
        'HandleVisibility', 'off');
    xline(ax, rptEnd, '--', 'Color', [0.45 0.45 0.45], 'LineWidth', 0.9, ...
        'HandleVisibility', 'off');
    if p == 1
        legend(ax, dispLabels, 'Location', 'northeast', 'Box', 'off', 'FontSize', 8);
    end
    if p == size(lifePanels, 1)
        xlabel(ax, 'Cycle number in second life');
    end
end

% Right column: C/20 reference tests, voltage only. All three cases are
% probed at the SAME cycle (defined by the fastest-dying case), so the panel
% title is that cycle number and the curves differ by case (colors as left).
stages = {'beginning'; 'middle'; 'ending'};
rptPos = [2 4 6];
for r = 1:numel(stages)
    ax = subplot(3, 2, rptPos(r)); hold(ax, 'on'); grid(ax, 'on');
    for i = 1:numel(cases)
        d = S.(cases{i}).rpt.(stages{r});
        plot(ax, d.time_h, d.voltage_V, 'Color', S.colors(i, :), 'LineWidth', 1.6);
    end
    title(ax, sprintf('Cycle %d', S.(cases{1}).rpt.(stages{r}).cycle));
    rightTags = {'(d)', '(e)', '(f)'};
    text(ax, 0.01, 1.07, rightTags{r}, 'Units', 'normalized', ...
        'FontWeight', 'bold', 'FontSize', 11);
    ylabel(ax, 'Voltage [V]');
    if r == numel(stages)
        xlabel(ax, 'RPT time [h]');
    end
end

base = fullfile(here, 'P4_03_delta_ratio');
savefig(f, [base '.fig']);
exportgraphics(f, [base '.png'], 'Resolution', 150);
close(f);

disp('Saved P4_03 delta-ratio combined figure (life + C/20)');
