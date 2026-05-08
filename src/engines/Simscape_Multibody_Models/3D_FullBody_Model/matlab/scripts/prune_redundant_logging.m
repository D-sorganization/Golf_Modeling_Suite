function out = prune_redundant_logging(model_name, opts)
%PRUNE_REDUNDANT_LOGGING  Disable redundant signal logging in MODEL_NAME.
%
%   OUT = PRUNE_REDUNDANT_LOGGING(MODEL_NAME, OPTS) walks the loaded
%   Simulink model MODEL_NAME and turns off LogSimulationData /
%   SignalLogging on blocks whose output is redundant or non-essential.
%   The audit in GitHub issue #4382 identified four categories:
%
%     1. Inertia sensors on cosmetic / non-critical solid bodies.
%     2. Per-axis duplicate logs that can be derived from a 3-vector.
%     3. Club force/torque logged in both local and global frames
%        (keep global only).
%     4. Velocity / acceleration logs where position + dt suffices.
%
%   The defaults below are conservative. Pass OPTS.aggressive=true to
%   also strip the velocity/acceleration mirrors of position channels.
%
%   This function mutates the loaded model in place unless
%   OPTS.dry_run=true. Caller must save_system afterward to persist
%   changes.
%
%   Args:
%       MODEL_NAME (char/string)  loaded Simulink model name.
%       OPTS (struct)
%         .verbose             default true; print each block touched.
%         .aggressive          default false; also disable vel/acc mirrors.
%         .dry_run             default false; only count, do not toggle.
%         .audit_report_path   optional JSON path for the audit report.
%         .source_model_path   optional source model path for reporting.
%         .target_model_path   optional target model path for reporting.
%
%   Returns:
%       OUT (struct)
%         .schema_version      report schema identifier.
%         .signals_disabled   count of candidates whose logging was on.
%         .blocks_removed     heuristic nonvirtual block savings estimate.
%         .heuristic_estimates separated estimate fields.
%         .measured_counts     before/after model counts, never heuristic.
%         .candidate_changes   machine-readable exact candidate paths.
%         .blocks_touched      compatibility list of touched paths.
%         .by_category         per-category candidate counts.
%
%   See also: BUILD_3D_FULLBODY, ADD_LEG_CHAIN, VALIDATE_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose');           opts.verbose           = true;  end
    if ~isfield(opts, 'aggressive');        opts.aggressive        = false; end
    if ~isfield(opts, 'dry_run');           opts.dry_run           = false; end
    if ~isfield(opts, 'audit_report_path'); opts.audit_report_path = "";    end
    if ~isfield(opts, 'source_model_path'); opts.source_model_path = "";    end
    if ~isfield(opts, 'target_model_path'); opts.target_model_path = "";    end

    if ~bdIsLoaded(char(model_name))
        error('prune_redundant_logging:notLoaded', ...
              'Model %s is not loaded. Call load_system first.', model_name);
    end

    model_file = local_model_file(model_name);
    if strlength(string(opts.target_model_path)) == 0
        opts.target_model_path = model_file.path;
    end
    if strlength(string(opts.source_model_path)) == 0
        opts.source_model_path = model_file.path;
    end

    before_counts = local_measure_model(model_name);

    out = local_empty_report(model_name, opts, model_file, before_counts);

    cosmetic_patterns = {'*Cosmetic*', '*Visual*', '*Marker*'};
    out = local_disable_in_blocks(model_name, cosmetic_patterns, ...
        'LogSimulationData', 'cosmetic_non_critical_body_logs', opts, out);

    redundant_axis_outports = { ...
        'HipPositionInputX',  'HipPositionInputY',  'HipPositionInputZ', ...
        'SpinePositionInputX','SpinePositionInputY', ...
        'LScapPositionInputX','LScapPositionInputY', ...
        'RScapPositionInputX','RScapPositionInputY', ...
        'LSPositionInputX','LSPositionInputY','LSPositionInputZ', ...
        'RSPositionInputX','RSPositionInputY','RSPositionInputZ', ...
        'LWPositionInputX','LWPositionInputY', ...
        'RWPositionInputX','RWPositionInputY'};
    for k = 1:numel(redundant_axis_outports)
        out = local_disable_outports_by_name(model_name, redundant_axis_outports{k}, ...
            'per_axis_duplicate_logs', opts, out);
    end

    duplicate_club_outports = { ...
        'ClubLocalForce', 'ClubLocalTorque', ...
        'ClubLocalAngularVel', 'ClubLocalAngularAcc'};
    for k = 1:numel(duplicate_club_outports)
        out = local_disable_outports_by_name(model_name, duplicate_club_outports{k}, ...
            'local_global_club_duplicates', opts, out);
    end

    if opts.aggressive
        vel_acc_outports = { ...
            'HipAngularVelocityX','HipAngularVelocityY','HipAngularVelocityZ', ...
            'HipAngularAccelerationX','HipAngularAccelerationY','HipAngularAccelerationZ', ...
            'TorsoAngularAcceleration', 'SpineAngularAccelerationX', ...
            'SpineAngularAccelerationY'};
        for k = 1:numel(vel_acc_outports)
            out = local_disable_outports_by_name(model_name, vel_acc_outports{k}, ...
                'optional_velocity_acceleration_mirrors', opts, out);
        end
    end

    out.measured_counts.after = local_measure_model(model_name);

    heuristic_blocks_removed = round(0.7 * out.signals_disabled);
    out.blocks_removed = heuristic_blocks_removed;
    out.heuristic_estimates = struct( ...
        'blocks_removed_estimate', heuristic_blocks_removed, ...
        'estimate_formula', 'round(0.7 * signals_disabled)', ...
        'is_measured', false);

    if opts.verbose
        fprintf('prune_redundant_logging:\n');
        fprintf('  dry_run = %s\n', char(string(opts.dry_run)));
        fprintf('  signals_disabled = %d\n', out.signals_disabled);
        fprintf('  blocks_removed (heuristic estimate) = %d\n', out.blocks_removed);
        f = fieldnames(out.by_category);
        for i = 1:numel(f)
            fprintf('    %-40s %d\n', f{i}, out.by_category.(f{i}));
        end
    end

    if strlength(string(opts.audit_report_path)) > 0
        local_write_json(opts.audit_report_path, out);
        out.audit_report_path = string(opts.audit_report_path);
        if opts.verbose
            fprintf('  audit_report_path = %s\n', opts.audit_report_path);
        end
    end
end


function out = local_empty_report(model_name, opts, model_file, before_counts)
    out = struct( ...
        'schema_version', "3d_fullbody_logging_audit.v1", ...
        'generated_at', string(datetime('now')), ...
        'model_name', string(model_name), ...
        'dry_run', logical(opts.dry_run), ...
        'aggressive', logical(opts.aggressive), ...
        'source_model', local_file_report(opts.source_model_path), ...
        'target_model', local_file_report(opts.target_model_path), ...
        'loaded_model_file', model_file, ...
        'signals_disabled', 0, ...
        'blocks_removed', 0, ...
        'heuristic_estimates', struct(), ...
        'measured_counts', struct('before', before_counts, 'after', before_counts), ...
        'disabled_block_paths', strings(0, 1), ...
        'disabled_outport_paths', strings(0, 1), ...
        'blocks_touched', strings(0, 1), ...
        'candidate_changes', repmat(local_change("", "", "", false), 0, 1), ...
        'by_category', struct( ...
            'cosmetic_non_critical_body_logs', 0, ...
            'per_axis_duplicate_logs', 0, ...
            'local_global_club_duplicates', 0, ...
            'optional_velocity_acceleration_mirrors', 0), ...
        'downstream_signal_requirements_preserved', [ ...
            "extractAllSignalsFromBus_required_channels"; ...
            "fit_swing_full_pipeline_required_channels"; ...
            "surrogate_dataset_generator_required_channels"; ...
            "optimizer_required_channels"; ...
            "matcher_required_channels"; ...
            "force_analysis_required_channels"], ...
        'notes', "Measured before/after counts are recorded separately from heuristic block-savings estimates.");
end


function out = local_disable_in_blocks(model_name, patterns, prop, category, opts, out)
    for k = 1:numel(patterns)
        try
            blocks = find_system(char(model_name), ...
                'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                'Type', 'block', 'Name', patterns{k});
        catch
            blocks = {};
        end
        for j = 1:numel(blocks)
            b = blocks{j};
            try
                cur = get_param(b, prop);
            catch
                continue
            end
            if ~strcmpi(cur, 'on'); continue; end
            if ~opts.dry_run
                set_param(b, prop, 'off');
            end
            out = local_record_change(out, category, "block", string(b), prop, ~opts.dry_run);
            if opts.verbose
                fprintf('  [%s] %s -> %s=off\n', category, b, prop);
            end
        end
    end
end


function out = local_disable_outports_by_name(model_name, outport_name, category, opts, out)
    try
        outports = find_system(char(model_name), ...
            'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
            'BlockType', 'Outport', 'Name', outport_name);
    catch
        outports = {};
    end
    for k = 1:numel(outports)
        b = outports{k};
        try
            ph = get_param(b, 'PortHandles');
            line = get_param(ph.Inport(1), 'Line');
            if line <= 0; continue; end
            src_port = get_param(line, 'SrcPortHandle');
            if src_port <= 0; continue; end
            cur = get_param(src_port, 'DataLogging');
            if ~strcmpi(cur, 'on'); continue; end
            if ~opts.dry_run
                set_param(src_port, 'DataLogging', 'off');
            end
            out = local_record_change(out, category, "outport", string(b), ...
                "SrcPortHandle.DataLogging", ~opts.dry_run);
            if opts.verbose
                fprintf('  [%s] %s -> DataLogging=off\n', category, b);
            end
        catch
            continue
        end
    end
end


function out = local_record_change(out, category, kind, path, property, mutated)
    out.signals_disabled = out.signals_disabled + 1;
    out.by_category.(char(category)) = out.by_category.(char(category)) + 1;
    out.blocks_touched(end+1, 1) = string(path);
    if kind == "block"
        out.disabled_block_paths(end+1, 1) = string(path);
    else
        out.disabled_outport_paths(end+1, 1) = string(path);
    end
    out.candidate_changes(end+1, 1) = local_change(category, kind, path, mutated);
    out.candidate_changes(end).property = string(property);
end


function change = local_change(category, kind, path, mutated)
    change = struct( ...
        'category', string(category), ...
        'kind', string(kind), ...
        'path', string(path), ...
        'property', "", ...
        'action', "set logging off", ...
        'mutated', logical(mutated));
end


function counts = local_measure_model(model_name)
    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    counts = struct( ...
        'total_blocks', numel(blocks), ...
        'nonvirtual_blocks', local_count_nonvirtual(blocks), ...
        'logged_signal_count', local_count_logged_signals(model_name));
end


function n = local_count_nonvirtual(blocks)
    n = 0;
    virtual_types = {'SubSystem', 'Mux', 'Demux', 'Inport', 'Outport', ...
                     'BusCreator', 'BusSelector', 'Goto', 'From', ...
                     'GotoTagVisibility', 'Terminator', 'Ground', ...
                     'EnablePort', 'TriggerPort', 'ActionPort'};
    for k = 1:numel(blocks)
        try
            bt = get_param(blocks{k}, 'BlockType');
        catch
            continue
        end
        if ~any(strcmp(bt, virtual_types))
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
    for k = 1:numel(ports)
        try
            if strcmpi(get_param(ports(k), 'DataLogging'), 'on')
                n = n + 1;
            end
        catch
        end
    end
end


function info = local_model_file(model_name)
    path = "";
    try
        path = string(get_param(char(model_name), 'FileName'));
    catch
    end
    info = local_file_report(path);
end


function info = local_file_report(path)
    path = string(path);
    info = struct( ...
        'path', path, ...
        'exists', false, ...
        'timestamp', "", ...
        'sha256', "");
    if strlength(path) == 0 || ~isfile(path)
        return
    end
    d = dir(path);
    info.exists = true;
    info.timestamp = string(d.date);
    info.sha256 = local_sha256(path);
end


function hash = local_sha256(path)
    try
        fid = fopen(path, 'r');
        cleaner = onCleanup(@() fclose(fid));
        bytes = fread(fid, Inf, 'uint8=>uint8');
        md = java.security.MessageDigest.getInstance('SHA-256');
        md.update(bytes);
        raw = typecast(md.digest(), 'uint8');
        hash = string(reshape(dec2hex(raw, 2).', 1, []));
        clear cleaner
    catch
        hash = "";
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
