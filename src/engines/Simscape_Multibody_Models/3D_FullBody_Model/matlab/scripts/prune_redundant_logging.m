function report = prune_redundant_logging(model_name, opts)
%PRUNE_REDUNDANT_LOGGING Disable redundant 3D fullbody logging with audit output.
%
%   REPORT = PRUNE_REDUNDANT_LOGGING(MODEL_NAME, OPTS) scans a loaded
%   Simulink model for known redundant logging surfaces and returns a
%   reproducible audit report. By default this is a dry run: candidates are
%   listed but the model is not mutated. Set OPTS.dry_run=false to disable
%   logging for the reported candidates.
%
%   The report keeps measured before/after counts separate from heuristic
%   savings. The legacy round(0.7 * signals_disabled) estimate is preserved
%   only under REPORT.heuristic_estimates and is never reported as a measured
%   block-count delta.
%
%   Options:
%     dry_run              default true
%     aggressive           default false; include optional velocity mirrors
%     verbose              default true
%     source_model_path    optional source .slx path for hash/timestamp
%     target_model_path    optional target .slx path for hash/timestamp
%     json_report_path     optional machine-readable JSON output path
%     markdown_report_path optional human-readable Markdown output path
%
%   See also VALIDATE_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    opts = local_defaults(opts);
    if ~bdIsLoaded(char(model_name))
        error('prune_redundant_logging:notLoaded', ...
              'Model %s is not loaded. Call load_system first.', model_name);
    end

    if strlength(opts.source_model_path) == 0
        opts.source_model_path = string(local_model_file(model_name));
    end
    if strlength(opts.target_model_path) == 0
        opts.target_model_path = string(local_model_file(model_name));
    end

    before_counts = local_measure_model(model_name);
    report = local_empty_report(model_name, opts, before_counts);

    report = local_scan_block_logging(model_name, ...
        ["*Cosmetic*", "*Visual*", "*Marker*"], ...
        "cosmetic_non_critical_body_logs", opts, report);

    axis_outports = [ ...
        "HipPositionInputX", "HipPositionInputY", "HipPositionInputZ", ...
        "SpinePositionInputX", "SpinePositionInputY", ...
        "LScapPositionInputX", "LScapPositionInputY", ...
        "RScapPositionInputX", "RScapPositionInputY", ...
        "LSPositionInputX", "LSPositionInputY", "LSPositionInputZ", ...
        "RSPositionInputX", "RSPositionInputY", "RSPositionInputZ", ...
        "LWPositionInputX", "LWPositionInputY", ...
        "RWPositionInputX", "RWPositionInputY"];
    report = local_scan_outport_logging(model_name, axis_outports, ...
        "per_axis_duplicate_logs", opts, report);

    club_outports = [ ...
        "ClubLocalForce", "ClubLocalTorque", ...
        "ClubLocalAngularVel", "ClubLocalAngularAcc"];
    report = local_scan_outport_logging(model_name, club_outports, ...
        "local_global_club_duplicates", opts, report);

    if opts.aggressive
        mirror_outports = [ ...
            "HipAngularVelocityX", "HipAngularVelocityY", "HipAngularVelocityZ", ...
            "HipAngularAccelerationX", "HipAngularAccelerationY", "HipAngularAccelerationZ", ...
            "TorsoAngularAcceleration", "SpineAngularAccelerationX", ...
            "SpineAngularAccelerationY"];
        report = local_scan_outport_logging(model_name, mirror_outports, ...
            "optional_velocity_acceleration_mirrors", opts, report);
    end

    report.measured_counts.after = local_measure_model(model_name);
    report.heuristic_estimates = local_heuristic_estimates(report);
    report.signals_disabled = numel(report.candidates);

    if opts.verbose
        local_print_summary(report);
    end
    if strlength(opts.json_report_path) > 0
        local_write_json(opts.json_report_path, report);
        report.artifacts.json_report_path = opts.json_report_path;
    end
    if strlength(opts.markdown_report_path) > 0
        local_write_markdown(opts.markdown_report_path, report);
        report.artifacts.markdown_report_path = opts.markdown_report_path;
    end
end


function opts = local_defaults(opts)
    if ~isfield(opts, 'dry_run');              opts.dry_run = true; end
    if ~isfield(opts, 'aggressive');           opts.aggressive = false; end
    if ~isfield(opts, 'verbose');              opts.verbose = true; end
    if ~isfield(opts, 'source_model_path');    opts.source_model_path = ""; end
    if ~isfield(opts, 'target_model_path');    opts.target_model_path = ""; end
    if ~isfield(opts, 'json_report_path');     opts.json_report_path = ""; end
    if ~isfield(opts, 'markdown_report_path'); opts.markdown_report_path = ""; end
    opts.source_model_path = string(opts.source_model_path);
    opts.target_model_path = string(opts.target_model_path);
    opts.json_report_path = string(opts.json_report_path);
    opts.markdown_report_path = string(opts.markdown_report_path);
end


function report = local_empty_report(model_name, opts, before_counts)
    report = struct( ...
        'schema_version', "3d_fullbody_logging_prune_audit.v1", ...
        'generated_at', string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z''')), ...
        'model_name', string(model_name), ...
        'dry_run', logical(opts.dry_run), ...
        'aggressive', logical(opts.aggressive), ...
        'source_model', local_file_info(opts.source_model_path), ...
        'target_model', local_file_info(opts.target_model_path), ...
        'measured_counts', struct('before', before_counts, 'after', before_counts), ...
        'heuristic_estimates', struct(), ...
        'signals_disabled', 0, ...
        'disabled_block_paths', strings(0, 1), ...
        'disabled_outport_paths', strings(0, 1), ...
        'candidates', repmat(local_candidate("", "", "", "", false), 0, 1), ...
        'category_breakdown', local_empty_breakdown(), ...
        'downstream_signal_requirements', local_downstream_requirements(), ...
        'artifacts', struct('json_report_path', "", 'markdown_report_path', ""), ...
        'notes', "Measured counts are model observations. Heuristic estimates are reported separately.");
end


function breakdown = local_empty_breakdown()
    breakdown = struct( ...
        'cosmetic_non_critical_body_logs', 0, ...
        'per_axis_duplicate_logs', 0, ...
        'local_global_club_duplicates', 0, ...
        'optional_velocity_acceleration_mirrors', 0);
end


function requirements = local_downstream_requirements()
    requirements = struct( ...
        'preserved', true, ...
        'allowlist', [ ...
            "CombinedSignalBus"; ...
            "ClubGlobalForce"; ...
            "ClubGlobalTorque"; ...
            "ClubGlobalAngularVel"; ...
            "ClubGlobalAngularAcc"; ...
            "HipPosition"; ...
            "SpinePosition"; ...
            "LScapPosition"; ...
            "RScapPosition"; ...
            "LSPosition"; ...
            "RSPosition"; ...
            "LWPosition"; ...
            "RWPosition"], ...
        'policy', "Disable only derivable duplicates and cosmetic/non-critical logs; preserve documented downstream analysis channels.");
end


function report = local_scan_block_logging(model_name, name_patterns, category, opts, report)
    for i = 1:numel(name_patterns)
        try
            blocks = find_system(char(model_name), ...
                'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                'Type', 'block', 'Name', char(name_patterns(i)));
        catch
            blocks = {};
        end
        for j = 1:numel(blocks)
            path = string(blocks{j});
            try
                current = string(get_param(path, 'LogSimulationData'));
            catch
                continue
            end
            if ~strcmpi(current, "on")
                continue
            end
            if ~opts.dry_run
                set_param(path, 'LogSimulationData', 'off');
            end
            report = local_record_candidate(report, category, "block", path, ...
                "LogSimulationData", ~opts.dry_run);
        end
    end
end


function report = local_scan_outport_logging(model_name, outport_names, category, opts, report)
    for i = 1:numel(outport_names)
        try
            outports = find_system(char(model_name), ...
                'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                'BlockType', 'Outport', 'Name', char(outport_names(i)));
        catch
            outports = {};
        end
        for j = 1:numel(outports)
            path = string(outports{j});
            try
                port_handle = local_source_port_for_outport(path);
                current = string(get_param(port_handle, 'DataLogging'));
            catch
                continue
            end
            if ~strcmpi(current, "on")
                continue
            end
            if ~opts.dry_run
                set_param(port_handle, 'DataLogging', 'off');
            end
            report = local_record_candidate(report, category, "outport", path, ...
                "SrcPortHandle.DataLogging", ~opts.dry_run);
        end
    end
end


function src_port = local_source_port_for_outport(outport_path)
    handles = get_param(outport_path, 'PortHandles');
    line = get_param(handles.Inport(1), 'Line');
    if line <= 0
        error('prune_redundant_logging:noLine', 'Outport has no source line.');
    end
    src_port = get_param(line, 'SrcPortHandle');
    if src_port <= 0
        error('prune_redundant_logging:noSourcePort', 'Outport has no source port.');
    end
end


function report = local_record_candidate(report, category, kind, path, property, mutated)
    report.candidates(end + 1, 1) = local_candidate(category, kind, path, property, mutated);
    report.category_breakdown.(char(category)) = report.category_breakdown.(char(category)) + 1;
    if kind == "block"
        report.disabled_block_paths(end + 1, 1) = path;
    else
        report.disabled_outport_paths(end + 1, 1) = path;
    end
end


function candidate = local_candidate(category, kind, path, property, mutated)
    candidate = struct( ...
        'category', string(category), ...
        'kind', string(kind), ...
        'path', string(path), ...
        'property', string(property), ...
        'action', "set logging off", ...
        'mutated', logical(mutated));
end


function estimates = local_heuristic_estimates(report)
    disabled_count = numel(report.candidates);
    estimates = struct( ...
        'disabled_signal_count', disabled_count, ...
        'estimated_nonvirtual_block_savings', round(0.7 * disabled_count), ...
        'formula', "round(0.7 * disabled_signal_count)", ...
        'is_measured', false);
end


function counts = local_measure_model(model_name)
    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    counts = struct( ...
        'total_blocks', local_count_report(numel(blocks), true), ...
        'nonvirtual_blocks', local_count_report(local_count_nonvirtual(blocks), true), ...
        'logged_signal_count', local_count_report(local_count_logged_signals(model_name), true));
end


function item = local_count_report(value, measured)
    item = struct('value', value, 'measured', logical(measured));
end


function n = local_count_nonvirtual(blocks)
    virtual_types = {'SubSystem', 'Mux', 'Demux', 'Inport', 'Outport', ...
                     'BusCreator', 'BusSelector', 'Goto', 'From', ...
                     'GotoTagVisibility', 'Terminator', 'Ground', ...
                     'EnablePort', 'TriggerPort', 'ActionPort'};
    n = 0;
    for i = 1:numel(blocks)
        try
            block_type = get_param(blocks{i}, 'BlockType');
        catch
            continue
        end
        if ~any(strcmp(block_type, virtual_types))
            n = n + 1;
        end
    end
end


function n = local_count_logged_signals(model_name)
    n = 0;
    try
        ports = find_system(char(model_name), ...
            'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
            'FindAll', 'on', 'Type', 'port');
    catch
        ports = [];
    end
    for i = 1:numel(ports)
        try
            if strcmpi(get_param(ports(i), 'DataLogging'), 'on')
                n = n + 1;
            end
        catch
        end
    end
end


function path = local_model_file(model_name)
    path = "";
    try
        path = string(get_param(char(model_name), 'FileName'));
    catch
    end
end


function info = local_file_info(path)
    path = string(path);
    info = struct('path', path, 'exists', false, 'timestamp', "", 'sha256', "");
    if strlength(path) == 0 || ~isfile(path)
        return
    end
    details = dir(path);
    info.exists = true;
    info.timestamp = string(details.date);
    info.sha256 = local_sha256(path);
end


function hash = local_sha256(path)
    hash = "";
    try
        fid = fopen(path, 'r');
        cleaner = onCleanup(@() fclose(fid));
        bytes = fread(fid, Inf, 'uint8=>uint8');
        digest = java.security.MessageDigest.getInstance('SHA-256');
        digest.update(bytes);
        raw = typecast(digest.digest(), 'uint8');
        hash = string(reshape(dec2hex(raw, 2).', 1, []));
        clear cleaner
    catch
    end
end


function local_write_json(path, payload)
    path = char(path);
    folder = fileparts(path);
    if strlength(string(folder)) > 0 && ~isfolder(folder)
        mkdir(folder);
    end
    fid = fopen(path, 'w');
    if fid < 0
        error('prune_redundant_logging:reportOpenFailed', ...
              'Could not open audit report for writing: %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', jsonencode(payload, 'PrettyPrint', true));
    clear cleaner
end


function local_write_markdown(path, report)
    path = char(path);
    folder = fileparts(path);
    if strlength(string(folder)) > 0 && ~isfolder(folder)
        mkdir(folder);
    end
    fid = fopen(path, 'w');
    if fid < 0
        error('prune_redundant_logging:markdownOpenFailed', ...
              'Could not open audit markdown report for writing: %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '# 3D FullBody Logging Prune Audit\n\n');
    fprintf(fid, '- Schema: `%s`\n', report.schema_version);
    fprintf(fid, '- Generated: `%s`\n', report.generated_at);
    fprintf(fid, '- Dry run: `%s`\n', string(report.dry_run));
    fprintf(fid, '- Source model: `%s`\n', report.source_model.path);
    fprintf(fid, '- Target model: `%s`\n\n', report.target_model.path);
    fprintf(fid, '## Measured Counts\n\n');
    fprintf(fid, '| Metric | Before | After |\n');
    fprintf(fid, '| --- | ---: | ---: |\n');
    fprintf(fid, '| Total blocks | %d | %d |\n', ...
        report.measured_counts.before.total_blocks.value, ...
        report.measured_counts.after.total_blocks.value);
    fprintf(fid, '| Nonvirtual blocks | %d | %d |\n', ...
        report.measured_counts.before.nonvirtual_blocks.value, ...
        report.measured_counts.after.nonvirtual_blocks.value);
    fprintf(fid, '| Logged signals | %d | %d |\n\n', ...
        report.measured_counts.before.logged_signal_count.value, ...
        report.measured_counts.after.logged_signal_count.value);
    fprintf(fid, '## Heuristic Estimate\n\n');
    fprintf(fid, '- Formula: `%s`\n', report.heuristic_estimates.formula);
    fprintf(fid, '- Estimated nonvirtual block savings: `%d`\n\n', ...
        report.heuristic_estimates.estimated_nonvirtual_block_savings);
    fprintf(fid, '## Candidates\n\n');
    for i = 1:numel(report.candidates)
        c = report.candidates(i);
        fprintf(fid, '- `%s` `%s` `%s` via `%s` mutated=`%s`\n', ...
            c.category, c.kind, c.path, c.property, string(c.mutated));
    end
    clear cleaner
end


function local_print_summary(report)
    fprintf('prune_redundant_logging audit\n');
    fprintf('  schema_version: %s\n', report.schema_version);
    fprintf('  dry_run: %s\n', string(report.dry_run));
    fprintf('  candidates: %d\n', numel(report.candidates));
    fprintf('  measured total blocks: %d -> %d\n', ...
        report.measured_counts.before.total_blocks.value, ...
        report.measured_counts.after.total_blocks.value);
    fprintf('  measured logged signals: %d -> %d\n', ...
        report.measured_counts.before.logged_signal_count.value, ...
        report.measured_counts.after.logged_signal_count.value);
    fprintf('  heuristic nonvirtual block savings: %d\n', ...
        report.heuristic_estimates.estimated_nonvirtual_block_savings);
end
