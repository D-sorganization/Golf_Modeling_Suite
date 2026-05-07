function [tbl, out] = leaderboard(records, varargin)
%LEADERBOARD Rank motion-matching fits using the canonical Metrics schema.
%
%   tbl = leaderboard(records) returns a sorted MATLAB table where each row
%   is a metrics.Metrics record.  Inputs may be:
%     - a string array of paths to JSON files containing Metrics records,
%     - a cell array of metrics.Metrics objects,
%     - a cell/struct array of legacy result structs (auto-converted via
%       metrics.Metrics.fromLegacyStruct for backwards compatibility).
%
%   tbl = leaderboard(records, 'SortBy', name) sorts by the given metric
%   field name (default: 'rmse_clubhead_mm', ascending).
%
%   tbl = leaderboard(results_dir, opts) scans a legacy results directory
%   containing *.mat files with a result struct and returns the issue #4080
%   compatibility table: swing_id, option, solver, rmse_mm, work_J, wall_s,
%   commit, timestamp.
%
%   See METRICS_SCHEMA.md for the canonical field set.

    out = [];
    if is_legacy_directory_call(records, varargin{:})
        opts = local_options_from_args(varargin{:});
        [tbl, out] = local_legacy_directory_table(records, opts);
        return;
    end

    p = inputParser();
    p.addParameter('SortBy', 'rmse_clubhead_mm', @(x) ischar(x) || isstring(x));
    p.parse(varargin{:});
    sortKey = char(p.Results.SortBy);

    items = local_normalize(records);
    if isempty(items)
        tbl = table();
        return;
    end

    fieldOrder = metrics.Metrics.FIELD_ORDER;
    rows = cell(numel(items), numel(fieldOrder));
    for i = 1:numel(items)
        m = items{i};
        for k = 1:numel(fieldOrder)
            rows{i, k} = m.(fieldOrder(k));
        end
    end
    tbl = cell2table(rows, 'VariableNames', cellstr(fieldOrder));
    if ismember(sortKey, tbl.Properties.VariableNames)
        tbl = sortrows(tbl, sortKey);
    end
end

function tf = is_legacy_directory_call(records, varargin)
    tf = (ischar(records) || (isstring(records) && isscalar(records))) && ...
        isfolder(records);
    if tf
        return;
    end
    tf = ~isempty(varargin) && isstruct(varargin{1});
end

function opts = local_options_from_args(varargin)
    opts = default_leaderboard_options();
    if ~isempty(varargin) && isstruct(varargin{1})
        user = varargin{1};
        names = fieldnames(user);
        for k = 1:numel(names)
            opts.(names{k}) = user.(names{k});
        end
    end
end

function [tbl, out] = local_legacy_directory_table(results_dir, opts)
    rows = {};
    files = dir(fullfile(string(results_dir), "**", "*.mat"));
    for i = 1:numel(files)
        path = fullfile(files(i).folder, files(i).name);
        try
            data = load(path);
            if ~isfield(data, "result")
                warning("leaderboard:missingResult", ...
                    "Skipping %s because it does not contain result", path);
                continue;
            end
            row = local_legacy_row(data.result);
            if opts.filter_swing_id ~= "" && row.swing_id ~= opts.filter_swing_id
                continue;
            end
            rows(end+1, :) = {row.swing_id, row.option, row.solver, ...
                row.rmse_mm, row.work_J, row.wall_s, row.commit, ...
                row.timestamp}; %#ok<AGROW>
        catch err
            warning("leaderboard:skipResult", ...
                "Skipping %s: %s", path, err.message);
        end
    end

    tbl = local_empty_legacy_table();
    if ~isempty(rows)
        tbl = cell2table(rows, 'VariableNames', ...
            tbl.Properties.VariableNames);
        sortBy = char(opts.sort_by);
        if ismember(sortBy, tbl.Properties.VariableNames)
            tbl = sortrows(tbl, sortBy);
        end
    end

    out = [];
    if opts.write_csv
        writetable(tbl, opts.csv_path);
    end
    if opts.format == "markdown"
        out = local_markdown_table(tbl);
    elseif opts.build_figure
        out = local_leaderboard_figure(tbl);
    end
end

function row = local_legacy_row(result)
    required = ["solver", "final_rmse_m"];
    for k = 1:numel(required)
        if ~isfield(result, required(k))
            error("leaderboard:missingField", ...
                "result missing required field %s", required(k));
        end
    end
    row = struct();
    row.swing_id = string(local_field(result, "swing_id", ""));
    row.option = double(local_field(result, "option", 0));
    row.solver = string(result.solver);
    row.rmse_mm = double(result.final_rmse_m) * 1000.0;
    row.work_J = double(local_field(result, "final_total_work_J", NaN));
    row.wall_s = double(local_field(result, "duration_s", NaN));
    row.commit = string(local_field(result, "git_commit", ""));
    row.timestamp = string(local_field(result, "timestamp_utc", ""));
end

function tbl = local_empty_legacy_table()
    tbl = table('Size', [0 8], ...
        'VariableTypes', {'string', 'double', 'string', 'double', ...
            'double', 'double', 'string', 'string'}, ...
        'VariableNames', {'swing_id','option','solver','rmse_mm', ...
            'work_J','wall_s','commit','timestamp'});
end

function value = local_field(s, name, defaultValue)
    if isfield(s, name)
        value = s.(name);
    else
        value = defaultValue;
    end
end

function md = local_markdown_table(tbl)
    names = string(tbl.Properties.VariableNames);
    lines = strings(0, 1);
    lines(end+1) = "| " + strjoin(names, " | ") + " |";
    lines(end+1) = "| " + strjoin(repmat("---", size(names)), " | ") + " |";
    for r = 1:height(tbl)
        vals = strings(1, numel(names));
        for c = 1:numel(names)
            vals(c) = string(tbl{r, c});
        end
        lines(end+1) = "| " + strjoin(vals, " | ") + " |"; %#ok<AGROW>
    end
    md = strjoin(lines, newline);
end

function fig = local_leaderboard_figure(tbl)
    fig = figure('Visible', 'off', 'Name', 'Motion Matching Leaderboard');
    uitable(fig, 'Data', tbl);
end

function items = local_normalize(records)
    if isstring(records)
        items = cell(numel(records), 1);
        for i = 1:numel(records)
            txt = fileread(char(records(i)));
            items{i} = metrics.Metrics.from_json(string(txt));
        end
        return;
    end
    if iscell(records)
        items = cell(numel(records), 1);
        for i = 1:numel(records)
            items{i} = local_coerce(records{i});
        end
        return;
    end
    if isstruct(records)
        items = cell(numel(records), 1);
        for i = 1:numel(records)
            items{i} = local_coerce(records(i));
        end
        return;
    end
    error("leaderboard:badInput", ...
        "records must be string array, cell array, or struct array");
end

function m = local_coerce(item)
    if isa(item, 'metrics.Metrics')
        m = item;
        return;
    end
    if isstruct(item)
        % Heuristic: legacy struct uses short field names.
        if isfield(item, 'rmse_clubhead') || isfield(item, 'rmse_butt')
            m = metrics.Metrics.fromLegacyStruct(item);
        else
            m = metrics.Metrics(item);
        end
        return;
    end
    if isstring(item) || ischar(item)
        m = metrics.Metrics.from_json(string(item));
        return;
    end
    error("leaderboard:badItem", "unsupported record type: %s", class(item));
end
