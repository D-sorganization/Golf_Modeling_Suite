function report = validate_3d_fullbody(model_name, opts)
%VALIDATE_3D_FULLBODY Validate 3D fullbody model counts and prune audit schema.
%
%   REPORT = VALIDATE_3D_FULLBODY(MODEL_NAME, OPTS) runs lightweight model
%   accounting checks and, when requested, embeds a dry-run logging-prune
%   audit report. The dry-run audit preserves the candidate list without
%   mutating the model.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose'); opts.verbose = true; end
    if ~isfield(opts, 'budget'); opts.budget = 1000; end
    if ~isfield(opts, 'include_logging_audit'); opts.include_logging_audit = true; end
    if ~isfield(opts, 'report_path'); opts.report_path = ""; end

    if ~bdIsLoaded(char(model_name))
        error('validate_3d_fullbody:notLoaded', ...
              'Model %s is not loaded.', model_name);
    end

    counts = local_measure_model(model_name);
    report = struct( ...
        'schema_version', "3d_fullbody_validation_report.v2", ...
        'generated_at', string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z''')), ...
        'model_name', model_name, ...
        'total_blocks', counts.total_blocks.value, ...
        'nonvirtual_blocks', counts.nonvirtual_blocks.value, ...
        'logged_signal_count', counts.logged_signal_count.value, ...
        'within_budget', counts.nonvirtual_blocks.value <= opts.budget, ...
        'logging_prune_audit', struct(), ...
        'passed', false);

    if opts.include_logging_audit
        audit_opts = struct('dry_run', true, 'verbose', false);
        report.logging_prune_audit = prune_redundant_logging(model_name, audit_opts);
        local_assert_audit_schema(report.logging_prune_audit);
    end

    report.passed = report.within_budget;
    if opts.verbose
        fprintf('validate_3d_fullbody:\n');
        fprintf('  total_blocks: %d\n', report.total_blocks);
        fprintf('  nonvirtual_blocks: %d / %d\n', report.nonvirtual_blocks, opts.budget);
        fprintf('  logged_signal_count: %d\n', report.logged_signal_count);
        fprintf('  passed: %s\n', string(report.passed));
    end

    if strlength(string(opts.report_path)) > 0
        local_write_json(opts.report_path, report);
    end
end


function local_assert_audit_schema(audit)
    required = [ ...
        "schema_version", ...
        "source_model", ...
        "target_model", ...
        "measured_counts", ...
        "heuristic_estimates", ...
        "disabled_block_paths", ...
        "disabled_outport_paths", ...
        "category_breakdown", ...
        "downstream_signal_requirements", ...
        "candidates"];
    for i = 1:numel(required)
        if ~isfield(audit, required(i))
            error('validate_3d_fullbody:missingAuditField', ...
                  'Logging prune audit missing required field: %s', required(i));
        end
    end
    if ~isfield(audit.heuristic_estimates, 'is_measured') || audit.heuristic_estimates.is_measured
        error('validate_3d_fullbody:heuristicReportedAsMeasured', ...
              'Heuristic estimates must remain separate from measured counts.');
    end
    if ~audit.downstream_signal_requirements.preserved
        error('validate_3d_fullbody:downstreamRequirementsNotPreserved', ...
              'Logging prune audit must preserve downstream signal requirements.');
    end
end


function counts = local_measure_model(model_name)
    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    counts = struct( ...
        'total_blocks', struct('value', numel(blocks), 'measured', true), ...
        'nonvirtual_blocks', struct('value', local_count_nonvirtual(blocks), 'measured', true), ...
        'logged_signal_count', struct('value', local_count_logged_signals(model_name), 'measured', true));
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


function local_write_json(path, payload)
    path = char(path);
    folder = fileparts(path);
    if strlength(string(folder)) > 0 && ~isfolder(folder)
        mkdir(folder);
    end
    fid = fopen(path, 'w');
    if fid < 0
        error('validate_3d_fullbody:reportOpenFailed', ...
              'Could not open validation report for writing: %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', jsonencode(payload, 'PrettyPrint', true));
    clear cleaner
end
