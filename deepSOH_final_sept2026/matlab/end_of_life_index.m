function k = end_of_life_index(capacity, capacityCut)
%END_OF_LIFE_INDEX  Last sample before the capacity first drops below capacityCut.
%   Trailing NaN (the padding of runs that end earlier) is ignored.
k = find(capacity < capacityCut, 1) - 1;
if isempty(k)
    k = find(~isnan(capacity), 1, 'last');
    warning('The run never drops below %.2f Ah; it is kept to its last sample.', capacityCut);
end
if k < 1
    error('The trajectory starts below %.2f Ah.', capacityCut);
end
end
