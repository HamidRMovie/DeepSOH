function [vbar, rnk] = prediction_variance(psi, measured, sigma, targets)
%PREDICTION_VARIANCE  Average prediction variance of eq. (25), for every horizon H.
%   psi       K x C x 5 sensitivities (eq. 20), one row per cycle
%   measured  channels recorded once per cycle (the measurement set M)
%   sigma     1-sigma uncertainty of one measurement of each recorded channel
%   targets   channels whose future is predicted, e.g. [iCap iRes]
%
%   With a record of the first H cycles,
%     W(H)    = sum over k <= H of Psi_M(k)' * R^-1 * Psi_M(k),  R = diag(sigma.^2)   (eq. 21)
%     vbar(H) = mean over k > H and over targets of Psi_m(k) * W(H)^-1 * Psi_m(k)'  (eq. 25)
%   vbar(H) is reported at the first predicted cycle, row H+1 of psi.
%
%   W is never formed as a matrix. The stacked noise-weighted rows D give W = D'*D, and
%   the SVD D = U*S*V' gives W^-1 = V*S^-2*V', which stays accurate when W is nearly
%   singular. While the record cannot yet determine all five states (rank < 5), vbar is NaN.

K = size(psi, 1);
w = 1 ./ sigma(:)';                    % weight of each recorded channel
vbar = nan(K - 1, 1);
rnk = zeros(K - 1, 1);
for H = 1:K - 1
    D = reshape(psi(1:H, measured, :) .* w, [], 5);
    [~, S, V] = svd(D, 'econ');
    s = diag(S);
    rnk(H) = sum(s > max(size(D)) * eps * s(1));
    if rnk(H) < 5
        continue
    end
    future = reshape(psi(H + 1:K, targets, :), [], 5);
    T = (future * V) ./ s';
    vbar(H) = mean(sum(T .^ 2, 2));
end
end
