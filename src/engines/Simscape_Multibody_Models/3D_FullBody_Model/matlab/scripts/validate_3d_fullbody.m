function out = validate_3d_fullbody(model_name, opts)
%VALIDATE_3D_FULLBODY  Production gate for the 3D_FullBody model.
%
%   OUT = VALIDATE_3D_FULLBODY(MODEL_NAME, OPTS) returns a versioned
%   validation report for the generated full-body Simscape model.  The
%   report is intentionally explicit enough for CI, MATLAB-only users, and
%   low-context follow-up agents to distinguish:
%
%     * scaffold phase: generated copy and logging prune are allowed to pass
%       without legs/contact.
%     * one_leg phase: at least one leg chain is required.
%     * full_contact phase: both legs and ground contact are required.
%
%   Default mode is scaffold so the current derivative build can merge while
%   later full-body phases ratchet the same gate instead of replacing it.
%
%   Key OPTS fields:
%       .budget               default 1000 (Simscape Home license cap)
%       .warning_budget       default 900
%       .phase                default "scaffold"; one of scaffold, one_leg,
%                             full_contact
%       .smoke_time           default 0.005 seconds; <= 0 skips smoke sim
%       .required_signals     string/cellstr allowlist of required signal
%                             name fragments
%       .enforce_required_signals
%                             default false in scaffold mode and true in
%                             production phases
%       .report_path          optional JSON report path
%       .source_model_path    source .slx path for timestamp/hash reporting
%       .target_model_path    generated .slx path for presence/timestamp
%
%   See also: BUILD_3D_FULLBODY, PRUNE_REDUNDANT_LOGGING, ADD_LEG_CHAIN.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    opts = local_fill_defaults(opts);

    if ~bdIsLoaded(char(model_name))
        error('validate_3d_fullbody:notLoaded', ...
              'Model %s is not loaded.', model_name);
    end

    out = local_blank_report(opts);

    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    [nonvirtual_count, class_counts] = local_count_nonvirtual_blocks(blocks);
    out.total_blocks = numel(blocks);
    out.total_block_count = out.total_blocks;
    out.nonvirtual_estimate = nonvirtual_count;
    out.nonvirtual_block_estimate = nonvirtual_count;
    out.block_type_counts = class_counts;
    out.within_budget = nonvirtual_count <= opts.budget;
    out.block_budget = local_block_budget_report(nonvirtual_count, opts);

    out.signal_inventory = local_signal_inventory(model_name, opts.required_signals);
    out.logged_signals = out.signal_inventory.signal_count;
    out.signal_count = out.signal_inventory.signal_count;
    out.required_signal_allowlist = out.signal_inventory.required_signal_allowlist;

    out.generated_model = local_generated_model_report(opts);
    out.leg_contact = local_leg_contact_report(model_name);

    out.smoke_sim = local_smoke_sim_report(model_name, opts.smoke_time);
    out.smoke_sim_status = out.smoke_sim.status;
    out.smoke_sim_message = out.smoke_sim.message;

    out.failure_messages = local_failure_messages(out, opts);
    out.warnings = local_warning_messages(out, opts);
    out.passed = isempty(out.failure_messages);

    if opts.verbose
        local_print_report(out);
    end

    if strlength(string(opts.report_path)) > 0
        local_write_json(opts.report_path, out);
        if opts.verbose
            fprintf('  validation_report_path = %s\n', opts.report_path);
        end
    end
end


function opts = local_fill_defaults(opts)
    if ~isfield(opts, 'verbose');           opts.verbose           = true;       end
    if ~isfield(opts, 'smoke_time');        opts.smoke_time        = 0.005;      end
    if ~isfield(opts, 'budget');            opts.budget            = 1000;       end
    if ~isfield(opts, 'warning_budget');    opts.warning_budget    = 900;        end
    if ~isfield(opts, 'phase');             opts.phase             = "scaffold"; end
    if ~isfield(opts, 'report_path');       opts.report_path       = "";         end
    if ~isfield(opts, 'source_model_path'); opts.source_model_path = "";         end
    if ~isfield(opts, 'target_model_path'); opts.target_model_path = "";         end
    if ~isfield(opts, 'required_signals')
        opts.required_signals = local_default_required_signals();
    end

    opts.phase = lower(string(opts.phase));
    allowed = ["scaffold", "one_leg", "full_contact"];
    if ~ismember(opts.phase, allowed)
        error('validate_3d_fullbody:invalidPhase', ...
              'Invalid phase "%s"; expected scaffold, one_leg, or full_contact.', ...
              opts.phase);
    end
    if opts.warning_budget > opts.budget
        error('validate_3d_fullbody:invalidWarningBudget', ...
              'warning_budget (%d) must be <= budget (%d).', ...
              opts.warning_budget, opts.budget);
    end
    if ~isfield(opts, 'enforce_required_signals')
        opts.enforce_required_signals = opts.phase ~= "scaffold";
    end
    opts.required_signals = string(opts.required_signals);
    opts.budget = double(opts.budget);
    opts.warning_budget = double(opts.warning_budget);
    opts.enforce_required_signals = logical(opts.enforce_required_signals);
end


function signals = local_default_required_signals()
    signals = [ ...
        "CombinedSignalBus"; ...
        "Club"; ...
        "Hip"; ...
        "Torso"; ...
        "Shoulder"; ...
        "Elbow"; ...
        "Wrist"];
end


function report = local_blank_report(opts)
    report = struct( ...
        'schema_version', "3d_fullbody_validation_report.v2", ...
        'generated_at', string(datetime('now', 'TimeZone', 'local')), ...
        'phase', string(opts.phase), ...
        'artifact_policy', "generated_only_ignored_by_git", ...
        'source_model_path', string(opts.source_model_path), ...
        'target_model_path', string(opts.target_model_path), ...
        'source_model_hash_sha256', local_sha256_file(opts.source_model_path), ...
        'total_blocks', 0, ...
        'total_block_count', 0, ...
        'nonvirtual_estimate', 0, ...
        'nonvirtual_block_estimate', 0, ...
        'nonvirtual_classification_method', ...
            "BlockType heuristic: all blocks except Simulink virtual routing/control shells", ...
        'home_license_budget', double(opts.budget), ...
        'warning_threshold', double(opts.warning_budget), ...
        'within_budget', false, ...
        'block_budget', struct(), ...
        'block_type_counts', struct(), ...
        'logged_signals', 0, ...
        'signal_count', 0, ...
        'signal_inventory', struct(), ...
        'required_signal_allowlist', struct(), ...
        'enforce_required_signals', opts.enforce_required_signals, ...
        'generated_model', struct(), ...
        'leg_contact', struct(), ...
        'smoke_sim', struct(), ...
        'smoke_sim_status', "skipped", ...
        'smoke_sim_message', "", ...
        'failure_messages', strings(0,1), ...
        'warnings', strings(0,1), ...
        'required_report_fields', local_required_report_fields(), ...
        'passed', false);
end


function fields = local_required_report_fields()
    fields = [ ...
        "schema_version"; ...
        "phase"; ...
        "generated_at"; ...
        "generated_model"; ...
        "source_model_hash_sha256"; ...
        "total_block_count"; ...
        "nonvirtual_block_estimate"; ...
        "nonvirtual_classification_method"; ...
        "home_license_budget"; ...
        "warning_threshold"; ...
        "block_budget"; ...
        "signal_count"; ...
        "required_signal_allowlist"; ...
        "leg_contact"; ...
        "smoke_sim"; ...
        "failure_messages"; ...
        "warnings"; ...
        "passed"];
end


function [count, class_counts] = local_count_nonvirtual_blocks(blocks)
    virtual_types = {'SubSystem', 'Mux', 'Demux', 'Inport', 'Outport', ...
                     'BusCreator', 'BusSelector', 'Goto', 'From', ...
                     'GotoTagVisibility', 'Terminator', 'Ground', ...
                     'EnablePort', 'TriggerPort', 'ActionPort'};
    count = 0;
    type_names = strings(0,1);
    for k = 1:numel(blocks)
        try
            bt = string(get_param(blocks{k}, 'BlockType'));
        catch
            bt = "Unknown";
        end
        type_names(end + 1, 1) = bt; %#ok<AGROW>
        if ~any(strcmp(char(bt), virtual_types))
            count = count + 1;
        end
    end
    class_counts = local_count_strings(type_names);
end


function counts = local_count_strings(values)
    counts = struct();
    unique_values = unique(values);
    for k = 1:numel(unique_values)
        name = matlab.lang.makeValidName(char(unique_values(k)));
        counts.(name) = sum(values == unique_values(k));
    end
end


function report = local_block_budget_report(nonvirtual_count, opts)
    if nonvirtual_count > opts.budget
        status = "over_budget";
    elseif nonvirtual_count > opts.warning_budget
        status = "warning";
    else
        status = "ok";
    end
    report = struct( ...
        'status', status, ...
        'nonvirtual_blocks', double(nonvirtual_count), ...
        'budget', double(opts.budget), ...
        'warning_threshold', double(opts.warning_budget), ...
        'headroom_to_budget', double(opts.budget - nonvirtual_count), ...
        'headroom_to_warning', double(opts.warning_budget - nonvirtual_count));
end


function report = local_signal_inventory(model_name, required_signals)
    logged = local_find_logged_signal_blocks(model_name);
    outports = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'BlockType', 'Outport');
    candidates = unique([string(logged(:)); string(outports(:))]);
    required = local_required_signal_report(candidates, required_signals);
    report = struct( ...
        'signal_count', double(numel(candidates)), ...
        'logged_block_count', double(numel(logged)), ...
        'outport_count', double(numel(outports)), ...
        'classification_method', ...
            "Unique blocks with DataLogging/LogSimulationData enabled plus Outport blocks", ...
        'sample_paths', candidates(1:min(numel(candidates), 30)), ...
        'required_signal_allowlist', required);
end


function logged = local_find_logged_signal_blocks(model_name)
    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    logged = strings(0,1);
    for k = 1:numel(blocks)
        if local_param_is_on(blocks{k}, 'DataLogging') || ...
                local_param_is_on(blocks{k}, 'LogSimulationData')
            logged(end + 1, 1) = string(blocks{k}); %#ok<AGROW>
        end
    end
end


function tf = local_param_is_on(block_path, param_name)
    try
        value = get_param(block_path, param_name);
        tf = strcmpi(char(value), 'on');
    catch
        tf = false;
    end
end


function report = local_required_signal_report(candidates, required_signals)
    present = strings(0,1);
    missing = strings(0,1);
    for k = 1:numel(required_signals)
        needle = string(required_signals(k));
        if any(contains(candidates, needle, 'IgnoreCase', true))
            present(end + 1, 1) = needle; %#ok<AGROW>
        else
            missing(end + 1, 1) = needle; %#ok<AGROW>
        end
    end
    report = struct( ...
        'required', required_signals(:), ...
        'present', present, ...
        'missing', missing, ...
        'passed', isempty(missing));
end


function report = local_generated_model_report(opts)
    target = string(opts.target_model_path);
    exists = strlength(target) > 0 && isfile(target);
    timestamp = "";
    bytes = 0;
    hash_value = "";
    if exists
        d = dir(target);
        timestamp = string(d.date);
        bytes = double(d.bytes);
        hash_value = local_sha256_file(target);
    end
    report = struct( ...
        'path', target, ...
        'exists', exists, ...
        'timestamp', timestamp, ...
        'bytes', bytes, ...
        'hash_sha256', hash_value);
end


function report = local_leg_contact_report(model_name)
    block_paths = string(find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block'));
    left_leg = any(contains(block_paths, ["Left Leg", "LHip", "LKnee", "LAnkle"], ...
        'IgnoreCase', true), 'all');
    right_leg = any(contains(block_paths, ["Right Leg", "RHip", "RKnee", "RAnkle"], ...
        'IgnoreCase', true), 'all');
    contact = any(contains(block_paths, ["Contact", "Ground", "Plane"], ...
        'IgnoreCase', true), 'all');
    if left_leg && right_leg && contact
        phase = "full_contact";
    elseif (left_leg || right_leg) && ~contact
        phase = "one_leg_no_contact";
    elseif left_leg || right_leg
        phase = "one_leg";
    else
        phase = "scaffold";
    end
    report = struct( ...
        'phase_detected', phase, ...
        'left_leg_present', left_leg, ...
        'right_leg_present', right_leg, ...
        'ground_contact_present', contact, ...
        'classification_method', ...
            "Block path fragments for Left/Right leg joint families and contact/ground blocks");
end


function report = local_smoke_sim_report(model_name, smoke_time)
    started = tic;
    report = struct( ...
        'status', "skipped", ...
        'duration_s', 0, ...
        'stop_time_s', double(smoke_time), ...
        'message', "");
    if smoke_time <= 0
        report.message = "smoke_time <= 0";
        return
    end
    try
        simIn = Simulink.SimulationInput(char(model_name));
        simIn = simIn.setModelParameter('StopTime', num2str(double(smoke_time)));
        simIn = simIn.setModelParameter('FastRestart', 'off');
        simOut = sim(simIn);
        report.duration_s = toc(started);
        if isprop(simOut, 'ErrorMessage') && ~isempty(simOut.ErrorMessage)
            report.status = "failed";
            report.message = string(simOut.ErrorMessage);
            return
        end
        if isprop(simOut, 'SimulationMetadata')
            md = simOut.SimulationMetadata;
            if isfield(md, 'ExecutionInfo') && isfield(md.ExecutionInfo, 'StopEvent')
                stop_event = string(md.ExecutionInfo.StopEvent);
                if ismember(stop_event, ["ReachedStopTime", "CompletedNormally", ...
                                         "SimulationStopped", "ExternalInputStopped"])
                    report.status = "success";
                else
                    report.status = "warning";
                    report.message = stop_event;
                end
            else
                report.status = "warning";
                report.message = "no SimulationMetadata.ExecutionInfo";
            end
        else
            report.status = "warning";
            report.message = "no SimulationMetadata";
        end
    catch ME
        report.duration_s = toc(started);
        report.status = "failed";
        report.message = string(ME.message);
    end
end


function failures = local_failure_messages(out, opts)
    failures = strings(0,1);
    if out.block_budget.status == "over_budget"
        failures(end + 1, 1) = sprintf( ...
            'Nonvirtual block estimate %d exceeds Home-license budget %d.', ...
            out.nonvirtual_block_estimate, opts.budget);
    end
    if out.enforce_required_signals && ~out.required_signal_allowlist.passed
        failures(end + 1, 1) = sprintf( ...
            'Missing required signal allowlist entries: %s.', ...
            strjoin(out.required_signal_allowlist.missing, ', '));
    end
    if out.smoke_sim.status == "failed"
        failures(end + 1, 1) = sprintf('Smoke simulation failed: %s', ...
            out.smoke_sim.message);
    end
    if opts.phase ~= "scaffold" && ~out.leg_contact.left_leg_present && ...
            ~out.leg_contact.right_leg_present
        failures(end + 1, 1) = sprintf( ...
            'Phase %s requires at least one scripted leg chain.', opts.phase);
    end
    if opts.phase == "full_contact" && ...
            (~out.leg_contact.left_leg_present || ...
             ~out.leg_contact.right_leg_present || ...
             ~out.leg_contact.ground_contact_present)
        failures(end + 1, 1) = ...
            "Phase full_contact requires left leg, right leg, and ground contact.";
    end
end


function warnings = local_warning_messages(out, opts)
    warnings = strings(0,1);
    if out.block_budget.status == "warning"
        warnings(end + 1, 1) = sprintf( ...
            'Nonvirtual block estimate %d is above warning threshold %d but below budget %d.', ...
            out.nonvirtual_block_estimate, opts.warning_budget, opts.budget);
    end
    if opts.phase == "scaffold" && ~out.leg_contact.left_leg_present && ...
            ~out.leg_contact.right_leg_present
        warnings(end + 1, 1) = ...
            "Leg/contact blocks are absent in scaffold mode; production phases must ratchet opts.phase.";
    end
    if ~out.enforce_required_signals && ~out.required_signal_allowlist.passed
        warnings(end + 1, 1) = sprintf( ...
            'Required signal allowlist has missing entries in non-enforcing mode: %s.', ...
            strjoin(out.required_signal_allowlist.missing, ', '));
    end
    if out.smoke_sim.status == "warning"
        warnings(end + 1, 1) = sprintf('Smoke simulation warning: %s', ...
            out.smoke_sim.message);
    end
    if strlength(out.generated_model.path) > 0 && ~out.generated_model.exists
        warnings(end + 1, 1) = sprintf( ...
            'Generated model path was provided but does not exist: %s.', ...
            out.generated_model.path);
    end
end


function local_print_report(out)
    fprintf('validate_3d_fullbody:\n');
    fprintf('  phase                 = %s\n', out.phase);
    fprintf('  total_blocks          = %d\n', out.total_block_count);
    fprintf('  nonvirtual_estimate   = %d  (warn %d, budget %d) -> %s\n', ...
        out.nonvirtual_block_estimate, out.warning_threshold, ...
        out.home_license_budget, out.block_budget.status);
    fprintf('  signal_count          = %d  allowlist -> %s\n', ...
        out.signal_count, ternary(out.required_signal_allowlist.passed, 'PASS', 'FAIL'));
    fprintf('  generated_model       = %s\n', ...
        ternary(out.generated_model.exists, 'present', 'missing'));
    fprintf('  legs/contact          = %s\n', out.leg_contact.phase_detected);
    fprintf('  smoke_sim             = %s (%.3fs)\n', ...
        out.smoke_sim.status, out.smoke_sim.duration_s);
    if ~isempty(out.failure_messages)
        fprintf('  failures:\n');
        for k = 1:numel(out.failure_messages)
            fprintf('    - %s\n', out.failure_messages(k));
        end
    end
    if ~isempty(out.warnings)
        fprintf('  warnings:\n');
        for k = 1:numel(out.warnings)
            fprintf('    - %s\n', out.warnings(k));
        end
    end
    fprintf('  passed                = %s\n', ternary(out.passed, 'true', 'false'));
end


function out = ternary(cond, a, b)
    if cond; out = a; else; out = b; end
end


function hash_value = local_sha256_file(path)
    hash_value = "";
    path = char(path);
    if isempty(path) || ~isfile(path)
        return
    end
    fid = fopen(path, 'rb');
    if fid < 0
        return
    end
    cleaner = onCleanup(@() fclose(fid));
    bytes = fread(fid, Inf, '*uint8');
    clear cleaner
    try
        md = java.security.MessageDigest.getInstance('SHA-256');
        md.update(bytes);
        digest = typecast(md.digest(), 'uint8');
        hash_value = string(lower(reshape(dec2hex(digest)', 1, [])));
    catch
        hash_value = "";
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
